import os
import math
import subprocess
import tempfile
import logging
from io import BytesIO
from memoize import delete_memoized

logger = logging.getLogger(__name__)

FFMPEG_BIN = os.getenv("FFMPEG_BIN", "ffmpeg")
FFPROBE_BIN = os.getenv("FFPROBE_BIN", "ffprobe")


def _duration_seconds_video(input_path: str) -> float:
    """
    Usa ffprobe para pegar a duração do arquivo em segundos.
    """
    result = subprocess.run(
        [
            FFPROBE_BIN,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            input_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def extract_representative_frames_from_video_url(
    video_url: str, max_frames: int = 3, delete_tmp_file: bool = True
):
    """
    Baixa o vídeo e extrai frames representativos (início, meio, fim).
    Retorna lista de tuplas (BytesIO_jpeg, timestamp_segundos).
    """
    from .file import save_tmp_file_from_url

    src_path, content = save_tmp_file_from_url(video_url)

    frames = []
    try:
        dur = _duration_seconds_video(src_path)
        if not math.isfinite(dur) or dur <= 0:
            dur = 3.0

        # timestamps simples: [0, meio, fim-0.2] limitado a max_frames
        ts = [0.0]
        if max_frames >= 2:
            ts.append(max(0.0, dur / 2.0))
        if max_frames >= 3:
            ts.append(max(0.0, dur - 0.2))
        ts = ts[:max_frames]

        for i, t in enumerate(ts):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_out:
                out_path = tmp_out.name
            cmd = [
                FFMPEG_BIN,
                "-y",
                "-ss",
                str(t),
                "-i",
                src_path,
                "-frames:v",
                "1",
                "-qscale:v",
                "3",  # jpeg de qualidade OK e leve
                out_path,
            ]
            subprocess.run(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True
            )
            with open(out_path, "rb") as f:
                img = BytesIO(f.read())
            img.name = f"frame_{i:03d}.jpg"
            img.seek(0)
            frames.append((img, float(t)))
            try:
                os.unlink(out_path)
            except FileNotFoundError:
                pass
    finally:
        if delete_tmp_file:
            try:
                os.unlink(src_path)
            except FileNotFoundError:
                pass

            delete_memoized(save_tmp_file_from_url, media_url=video_url)

    return frames
