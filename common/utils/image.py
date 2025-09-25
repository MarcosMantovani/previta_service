import threading
import cv2
import pytesseract
import numpy as np
import logging
from PIL import Image, ImageFilter, ImageOps
import re
import os
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)
cv2.setNumThreads(1)
_OCR_SEMAPHORE = threading.Semaphore(1)


def enhance_image(img: Image.Image, max_side: int = 1024) -> Image.Image:
    """Deskew leve + CLAHE + nitidez. Mantém cor (assinaturas/carabimbos)."""
    # 1) aumenta contraste
    img_eq = ImageOps.autocontrast(img, cutoff=2)
    # 2) de-noise leve
    img_sharp = img_eq.filter(ImageFilter.UnsharpMask(radius=2, percent=150))
    # 3) resize mantendo proporção (lado máx. 1024 px)
    img_sharp.thumbnail((max_side, max_side))
    return img_sharp


def _ensure_300dpi(img: Image.Image, target_dpi: int = 300) -> Image.Image:
    # Se não houver DPI definido, assume 72
    dpi = img.info.get("dpi", (72, 72))[0] or 72
    if dpi >= target_dpi:
        return img
    scale = target_dpi / dpi
    new_size = (int(img.width * scale), int(img.height * scale))
    return img.resize(new_size, Image.LANCZOS)


def _binarize(img: Image.Image) -> Image.Image:
    # conversão para OpenCV (grayscale já garantido)
    np_img = np.array(img)
    # Redução de ruído leve
    np_img = cv2.medianBlur(np_img, 3)
    # Limiar adaptativo robusto para documentos
    thr = cv2.adaptiveThreshold(
        np_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 35, 15
    )
    return Image.fromarray(thr)


def _preprocess_for_ocr(img: Image.Image) -> Image.Image:
    # 1) garantir 300 DPI e escala adequada
    img = _ensure_300dpi(img)
    # 2) converter para tons de cinza
    img = ImageOps.grayscale(img)
    # 3) autocontraste e leve nitidez
    img = ImageOps.autocontrast(img, cutoff=0.5)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=150, threshold=3))
    # 4) binarização
    img = _binarize(img)
    return img


def _fix_orientation(img: Image.Image) -> Image.Image:
    """Tenta detectar rotação com OSD do Tesseract e corrigir."""
    try:
        osd = pytesseract.image_to_osd(img)
        m = re.search(r"Rotate:\s+(\d+)", osd)
        if m:
            angle = int(m.group(1)) % 360
            if angle:
                # Tesseract indica rotação necessária em graus (clockwise).
                return img.rotate(360 - angle, expand=True)
    except Exception:
        pass
    return img


# ---------- Fatiamento seguro (lida com imagens enormes/alongadas) ----------


def _slice_for_ocr(
    img: Image.Image,
    max_dim: int = 8000,
    stripe: int = 2200,
    overlap: int = 100,
) -> List[Tuple[Tuple[int, int, int, int], Image.Image]]:
    """
    Devolve cortes (box, tile_img) para OCR.
    - evita limites do Tesseract (dimensão/área)
    - usa tiras verticais para páginas muito largas; horizontais para muito altas
    - se a imagem já for "pequena", retorna 1 tile
    """
    w, h = img.size
    # área limite (~64MP) para evitar estouro de memória
    if (max(w, h) <= max_dim) and (w * h <= 64_000_000):
        return [((0, 0, w, h), img)]

    tiles = []
    if w >= h and (w > max_dim or w / max(1, h) >= 3.0):
        # Tiras verticais
        x = 0
        step = stripe - overlap
        while x < w:
            x2 = min(x + stripe, w)
            box = (x, 0, x2, h)
            tiles.append((box, img.crop(box)))
            if x2 == w:
                break
            x += step
    elif h > max_dim or h / max(1, w) >= 3.0:
        # Tiras horizontais
        y = 0
        step = stripe - overlap
        while y < h:
            y2 = min(y + stripe, h)
            box = (0, y, w, y2)
            tiles.append((box, img.crop(box)))
            if y2 == h:
                break
            y += step
    else:
        # Grid simples 2x2 para áreas muito grandes
        midx = w // 2
        midy = h // 2
        boxes = [
            (0, 0, midx, midy),
            (midx, 0, w, midy),
            (0, midy, midx, h),
            (midx, midy, w, h),
        ]
        for b in boxes:
            tiles.append((b, img.crop(b)))
    return tiles


def _tesseract(
    img: Image.Image,
    lang: str = "por+eng",
    psm: int = 6,
    oem: int = 3,
    tessdata_dir: Optional[str] = None,
) -> str:
    if tessdata_dir:
        os.environ["TESSDATA_PREFIX"] = tessdata_dir
    config = f"--oem {oem} --psm {psm} -c load_system_dawg=0 -c load_freq_dawg=0"
    return pytesseract.image_to_string(img, lang=lang, config=config)


def _normalize_pixels(
    img: Image.Image,
    target_long_side: int = 2200,
    max_long_side: int = 3000,
    allow_upscale: bool = False,
) -> Image.Image:
    """
    Normaliza por pixels, não por DPI.
    - Se o lado maior > max_long_side -> downscale
    - Se allow_upscale=True e lado maior < target_long_side -> upscale moderado
    - Caso contrário, retorna como está.
    """
    w, h = img.size
    long_side = max(w, h)

    if long_side > max_long_side:
        scale = max_long_side / float(long_side)
        return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    if allow_upscale and long_side < target_long_side:
        scale = target_long_side / float(long_side)
        return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    return img


def extract_text_from_image(
    img: Image.Image,
    lang: str = "por+eng",
    psm: int = 6,
    oem: int = 3,
    tessdata_dir: Optional[str] = None,
) -> str:

    img_norm = _normalize_pixels(
        img, target_long_side=2200, max_long_side=3000, allow_upscale=False
    )
    oriented = _fix_orientation(ImageOps.grayscale(img_norm))

    # 3) Pré-processar
    pre = _preprocess_for_ocr(oriented)

    # 4) Fatiar se necessário e OCR tile a tile
    pieces = _slice_for_ocr(pre, max_dim=8000, stripe=2200, overlap=100)

    # Heurística de ordenação: blocos por top->bottom, left->right
    pieces_sorted = sorted(pieces, key=lambda it: (it[0][1], it[0][0]))

    out = []
    for _, tile in pieces_sorted:
        try:
            out.append(
                _tesseract(
                    tile, lang=lang, psm=psm, oem=oem, tessdata_dir=tessdata_dir
                ).strip()
            )
        except pytesseract.TesseractError:
            # fallback: reduzir um pouco e tentar de novo
            tw, th = tile.size
            fallback = tile.resize((int(tw * 0.8), int(th * 0.8)), Image.LANCZOS)
            out.append(
                _tesseract(
                    fallback, lang=lang, psm=psm, oem=oem, tessdata_dir=tessdata_dir
                ).strip()
            )
    return "\n".join([t for t in out if t])
