# Imports para manter compatibilidade com código existente
# Este arquivo permite que imports como "from common.utils import function_name" continuem funcionando

# Base utilities (data manipulation, business days)
from .base import (
    is_business_day,
    get_next_business_day,
    get_next_month_day,
    to_dict,
    from_dict,
    to_dataclass,
    calendar,
    T,
)

# Text processing
from .text import (
    sanitize_string,
    estimate_strings_similarity,
    replace_accents_characters,
    normalize_mathematical_text,
    format_phone_number,
)

# HTTP requests
from .requests import (
    retry_on_failure,
    url_to_buffer,
)

# Image processing
from .image import (
    extract_text_from_image,
    enhance_image,
)

# Audio processing
from .audio import (
    get_mp3_from_media_url,
    get_audio_duration_from_mp3_bytes,
    convert_generator_to_mp3_bytes,
    convert_mp3_to_base64,
    get_mean_volume_from_audio_file,
    get_duration_seconds_from_audio_file,
    file_has_audio_stream,
    FFMPEG_BIN,
    FFPROBE_BIN,
    RNNOISE_MODEL,
    _VAD_FILTER,
)

# Video processing
from .video import (
    extract_representative_frames_from_video_url,
)

# Document processing
from .document import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_xlsx,
    convert_document_url_to_text,
)

# File handling
from .file import save_tmp_file_from_url

# Task management
from .task import (
    is_task_running_or_waiting,
    cancel_previous_tasks,
    acquire_lock,
    release_lock,
)

# Manter todas as funções disponíveis no namespace principal
__all__ = [
    # Base
    "is_business_day",
    "get_next_business_day",
    "get_next_month_day",
    "to_dict",
    "from_dict",
    "to_dataclass",
    "calendar",
    "T",
    # Text
    "sanitize_string",
    "estimate_strings_similarity",
    "replace_accents_characters",
    "normalize_mathematical_text",
    "format_phone_number",
    # Requests
    "retry_on_failure",
    "url_to_buffer",
    # Image
    "extract_text_from_image",
    "_looks_like_document",
    "enhance_image",
    # Audio
    "get_mp3_from_media_url",
    "get_audio_duration_from_mp3_bytes",
    "convert_generator_to_mp3_bytes",
    "convert_mp3_to_base64",
    "get_mean_volume_from_audio_file",
    "get_duration_seconds_from_audio_file",
    "file_has_audio_stream",
    "FFMPEG_BIN",
    "FFPROBE_BIN",
    "RNNOISE_MODEL",
    "_VAD_FILTER",
    # Video
    "extract_representative_frames_from_video_url",
    # Document
    "extract_text_from_pdf",
    "extract_text_from_docx",
    "extract_text_from_xlsx",
    "convert_document_url_to_text",
    # File
    "save_tmp_file_from_url",
    # Task
    "is_task_running_or_waiting",
    "cancel_previous_tasks",
    "acquire_lock",
    "release_lock",
]
