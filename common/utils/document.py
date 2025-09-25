import cv2
import numpy as np
import base64
import statistics
import time
import gc
import logging
import traceback
from PIL import Image
import fitz  # PyMuPDF
import docx
import pandas as pd
from typing import List, Tuple
from io import BytesIO
from memoize import memoize

from common.utils.image import enhance_image, extract_text_from_image
from common.utils.requests import url_to_buffer

logger = logging.getLogger(__name__)


class DocumentTextError(Exception):
    pass


def _render_pdf_page_to_pil(
    page: fitz.Page,
    target_long_side: int = 2000,
    max_long_side: int = 3000,
    grayscale: bool = True,
) -> Image.Image:
    """Render leve da página (print), lado maior limitado."""
    rect = page.rect
    long_pts = max(rect.width, rect.height)
    zoom = max(
        0.5, min(target_long_side / float(long_pts), max_long_side / float(long_pts))
    )
    mat = fitz.Matrix(zoom, zoom)
    cs = fitz.csGRAY if grayscale else fitz.csRGB
    pix = page.get_pixmap(matrix=mat, colorspace=cs, alpha=False)
    mode = "L" if grayscale else "RGB"
    img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)

    w, h = img.size
    long_side = max(w, h)
    if long_side > max_long_side:
        scale = max_long_side / float(long_side)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return img


# ----------------- OCR orçamentado por página -----------------


def ocr_page_budgeted(
    page: fitz.Page,
    lang: str = "por",
    time_budget_s: float = 6.0,
    conf_target: float = 70.0,
) -> Tuple[str, float, Image.Image]:
    """
    Executa OCR numa página com limite de tempo e escalonamento de custo:
      1) tenta texto nativo (0 custo)
      2) OCR "fast" (psm=6)
      3) se conf < alvo, OCR "psm=4" (duas colunas)
      4) se conf ainda baixo e img muito longa/larga, fatiar e juntar
    Para não estressar CPU, SEMPRE sem upscale por DPI e com semáforo.
    """
    t0 = time.monotonic()

    # 0) texto nativo (quase de graça)
    native = page.get_text("text") or ""
    if native.strip():
        return native.strip(), 100.0, None

    # 1) render leve
    img = _render_pdf_page_to_pil(
        page, target_long_side=2000, max_long_side=2800, grayscale=True
    )

    # FAST: psm=6
    txt, conf = extract_text_from_image(
        img, lang=lang, psm=6, oem=1, extra_config="", mode="fast"
    )
    if conf >= conf_target or (time.monotonic() - t0) > time_budget_s:
        return txt, conf, img

    # COLUNAS: psm=4
    txt2, conf2 = extract_text_from_image(
        img, lang=lang, psm=4, oem=1, extra_config="", mode="strong"
    )
    if conf2 >= conf_target or (time.monotonic() - t0) > time_budget_s:
        return txt2, conf2, img

    from common.utils.image import slice_image_if_needed

    # FATIA se realmente grande/alongada
    tiles = slice_image_if_needed(img, max_dim=7000, stripe=2600, overlap=80)
    out_parts: List[str] = []
    confs: List[float] = []
    for _, tile in sorted(tiles, key=lambda b: (b[0][1], b[0][0])):
        if (time.monotonic() - t0) > time_budget_s:
            break
        txt_t, conf_t = extract_text_from_image(tile, lang=lang, psm=4, oem=1)
        out_parts.append(txt_t)
        confs.append(conf_t)

    joined = " ".join([p for p in out_parts if p]).strip()
    mean_conf = statistics.mean(confs) if confs else 0.0
    return joined, mean_conf, img


def extract_text_from_pdf(
    file_content: bytes, lang: str = "por"
) -> Tuple[str, list[str]]:
    """
    Extrai texto de PDF com fallback pra OCR leve página a página.
    - Usa renderização controlada (cinza, lado máx. ~3000 px).
    """

    final_text = ""
    out_pages = []
    base64_images = []

    with fitz.open(stream=file_content, filetype="pdf") as doc:
        if doc.needs_pass:
            raise DocumentTextError("PDF is password protected.")

        def extract_text_and_images(page, attempt=1):

            text = None
            img = None
            print(f"Attempt {attempt}")

            if attempt == 1:
                text = page.get_text("text") or ""

            elif attempt == 2:
                images = page.get_images(full=True)
                total_images = len(images)
                if total_images > 0:
                    if total_images <= 2:
                        textpage = page.get_textpage_ocr(
                            full=True, dpi=300, language="por"
                        )
                        text = textpage.extractTEXT()
                        text = text.strip()
            elif attempt == 3:
                img = _render_pdf_page_to_pil(
                    page, target_long_side=2000, max_long_side=2800, grayscale=True
                )
                text = extract_text_from_image(img, lang=lang, psm=6, oem=1)

                text = text.strip()
                if not text:
                    text = None

            attempt += 1
            return text, img, attempt

        for pno in range(doc.page_count):

            page = doc.load_page(pno)
            attempt = 1
            while attempt <= 4:
                text, img, attempt = extract_text_and_images(page, attempt)
                if text:
                    out_pages.append(f"Page {pno+1}:\n{text}")
                    print(f"Page {pno+1}: {text}")
                    break

            if not text and img:
                ocr_img = enhance_image(img, max_side=1024)

                with BytesIO() as buf:
                    ocr_img.save(buf, "jpeg", quality=85)
                    base64_images.append(base64.b64encode(buf.getvalue()).decode())

                del ocr_img
                del img
                gc.collect()

    if out_pages:
        final_text = "\n\n".join(out_pages).strip()

    return final_text, base64_images


def extract_text_from_docx(file_content: bytes) -> str:
    text = ""
    try:
        doc = docx.Document(BytesIO(file_content))
        for paragraph in doc.paragraphs:
            text += paragraph.text
    except Exception as e:
        logger.error(f"Error extracting text from docx: {str(e)}")

    return text


def extract_text_from_xlsx(file_content: bytes) -> str:
    text = ""

    try:
        for sheet_name in pd.ExcelFile(file_content).sheet_names:
            df = pd.read_excel(file_content, sheet_name=sheet_name)
            text += f"Sheet: {sheet_name}\n\n{df.to_string()}\n\n"
    except Exception as e:
        logger.error(f"Error extracting text from xlsx: {str(e)}")

    return text


@memoize()
def convert_document_url_to_text(file_url: str) -> Tuple[str, str, list[str]]:
    """
    Converts a file URL to text.

    can handle text files (txt, pdf, docx, etc), and also xlsx files
    """

    # retrieve file content from url
    file_content, headers = url_to_buffer(file_url)
    extracted_text = None
    file_type = None

    # check mime type
    mime_type = headers.get("Content-Type")

    base64_images = []

    if mime_type == "application/pdf":
        extracted_text, base64_images = extract_text_from_pdf(file_content)
        file_type = "pdf"
    elif (
        mime_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        extracted_text = extract_text_from_docx(file_content)
        file_type = "docx"
    elif (
        mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ):
        extracted_text = extract_text_from_xlsx(file_content)
        file_type = "xlsx"
    elif mime_type == "text/plain":
        extracted_text = file_content.decode("utf-8")
        file_type = "txt"
    elif "image" in mime_type:
        extracted_text = ""
        file_type = "image"
    else:
        logger.warning(f"Unsupported file type: {mime_type}")

    return extracted_text, file_type, base64_images
