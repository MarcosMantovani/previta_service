import os
import subprocess
import tempfile
import logging
from io import BytesIO
from typing import Tuple, Any, Iterator
from types import GeneratorType
import base64
from urllib.parse import urlparse
from pydub import AudioSegment
from memoize import memoize, delete_memoized

logger = logging.getLogger(__name__)

FFMPEG_BIN = os.getenv("FFMPEG_BIN", "ffmpeg")
FFPROBE_BIN = os.getenv("FFPROBE_BIN", "ffprobe")
RNNOISE_MODEL = os.getenv("RNNOISE_MODEL", "/usr/local/share/rnnoise-model.rnn")

_VAD_FILTER = (
    "silenceremove="
    "start_periods=1:start_duration=0:"
    "start_threshold=-45dB:"
    "stop_periods=1:stop_duration=0.4:"
    "stop_threshold=-45dB:"
    "detection=peak"
)


@memoize()
def get_mean_volume_from_audio_file(input_path: str) -> float:
    """
    Usa ffmpeg+volumedetect para medir o volume médio (dBFS).
    """
    result = subprocess.run(
        [FFMPEG_BIN, "-i", input_path, "-af", "volumedetect", "-f", "null", "-"],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    for line in result.stderr.splitlines():
        if "mean_volume:" in line:
            # ex.: "mean_volume: -23.4 dB"
            return float(line.split(":")[1].split()[0])
    # fallback seguro
    return 0.0


@memoize()
def get_duration_seconds_from_audio_file(input_path: str) -> float:
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


@memoize()
def file_has_audio_stream(path: str) -> bool:
    """
    True se o arquivo tiver pelo menos uma trilha de áudio.
    """
    out = subprocess.run(
        [
            FFPROBE_BIN,
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return bool(out.stdout.strip())


@memoize()
def get_mp3_from_media_url(
    media_url: str, use_vad: bool = False, delete_tmp_file: bool = True
):
    """
    Baixa áudio OU vídeo, extrai/normaliza o ÁUDIO e devolve MP3.
    Retorna: (BytesIO, duração_segundos) - 16 kHz | mono | 64 kb/s.
    """
    from .file import save_tmp_file_from_url

    src_path, content = save_tmp_file_from_url(media_url)

    try:
        # 0) checa se há trilha de áudio
        if not file_has_audio_stream(src_path):
            raise RuntimeError("Arquivo não possui trilha de áudio.")

        # 1) ganho/denoise -------------------------------------------------------
        mean_db = get_mean_volume_from_audio_file(src_path)
        needs_gain = mean_db < -35.0

        filters = ["highpass=f=80"]
        if needs_gain:
            filters.extend(
                [
                    "loudnorm=I=-16:LRA=11:TP=-1.5",
                    f"arnndn=m={RNNOISE_MODEL}",
                ]
            )
        if use_vad:
            filters.append(_VAD_FILTER)

        filter_chain = ",".join(filters)

        # 2) recodifica (dropa vídeo com -vn) -----------------------------------
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_out:
            dst_path = tmp_out.name

        cmd = [
            FFMPEG_BIN,
            "-y",
            "-i",
            src_path,
            "-vn",  # ignora vídeo
            "-ar",
            "16000",
            "-ac",
            "1",
            "-af",
            filter_chain,
            "-c:a",
            "libmp3lame",
            "-b:a",
            "64k",
            dst_path,
        ]
        subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True
        )

        # 3) retorno -------------------------------------------------------------
        with open(dst_path, "rb") as f:
            mp3_bytes = BytesIO(f.read())
        duration = get_duration_seconds_from_audio_file(dst_path)

        # 4) limpeza -------------------------------------------------------------
        for p in (src_path, dst_path):
            if not delete_tmp_file and p == src_path:
                continue
            else:
                delete_memoized(save_tmp_file_from_url, media_url=media_url)
            try:
                os.unlink(p)
            except FileNotFoundError:
                pass

    except Exception as e:
        logger.warning(f"FFmpeg media->mp3 failed: {e}. Fallback via pydub.")
        try:
            if delete_tmp_file:
                try:
                    os.unlink(src_path)
                except FileNotFoundError:
                    pass

                delete_memoized(save_tmp_file_from_url, media_url=media_url)
            # pydub tenta decodificar; se for vídeo sem áudio, vai falhar também
            audio = AudioSegment.from_file(BytesIO(content))
            audio = audio.set_channels(1).set_frame_rate(16000)
            mp3_buffer = BytesIO()
            audio.export(mp3_buffer, format="mp3", bitrate="64k")
            mp3_bytes = mp3_buffer
            duration = len(audio) / 1000.0
        except Exception as fallback_error:
            logger.error(f"Fallback conversion failed: {fallback_error}")
            raise

    filename = os.path.basename(urlparse(media_url).path) or "media"
    if not filename.lower().endswith(".mp3"):
        filename = os.path.splitext(filename)[0] + ".mp3"
    mp3_bytes.name = filename
    mp3_bytes.seek(0)
    return mp3_bytes, duration


def get_audio_duration_from_mp3_bytes(mp3_bytes: bytes) -> float:
    """
    Get the duration of an MP3 file.
    """
    audio = AudioSegment.from_file(BytesIO(mp3_bytes))
    return audio.duration_seconds


def convert_generator_to_mp3_bytes(
    iterator: GeneratorType | Iterator[bytes],
) -> Tuple[bytes, float]:
    """
    Converts a generator to an MP3 bytes.
    """
    audio_stream = BytesIO()
    for chunk in iterator:
        audio_stream.write(chunk)
    mp3_bytes = audio_stream.getvalue()

    return mp3_bytes, get_audio_duration_from_mp3_bytes(mp3_bytes)


# BytesIO or bytes or GeneratorType
def convert_mp3_to_base64(
    mp3_bytes: BytesIO | bytes | GeneratorType | Iterator[bytes],
) -> str:
    """
    Converts an MP3 file to a base64 string.
    """
    if isinstance(mp3_bytes, BytesIO):
        return (
            f"data:audio/mp3;base64,{base64.b64encode(mp3_bytes.getvalue()).decode('utf-8')}",
            get_audio_duration_from_mp3_bytes(mp3_bytes.getvalue()),
        )
    elif isinstance(mp3_bytes, bytes):
        return (
            f"data:audio/mp3;base64,{base64.b64encode(mp3_bytes).decode('utf-8')}",
            get_audio_duration_from_mp3_bytes(mp3_bytes),
        )
    elif isinstance(mp3_bytes, GeneratorType) or isinstance(mp3_bytes, Iterator):

        audio_stream = BytesIO()

        for chunk in mp3_bytes:
            if chunk:
                audio_stream.write(chunk)

        audio_stream.seek(0)

        return (
            f"data:audio/mp3;base64,{base64.b64encode(audio_stream.getvalue()).decode('utf-8')}",
            get_audio_duration_from_mp3_bytes(audio_stream.getvalue()),
        )
    else:
        raise Exception(f"Invalid type: {type(mp3_bytes)}")
