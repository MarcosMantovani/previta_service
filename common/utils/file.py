import tempfile
import logging
from typing import Tuple
from memoize import memoize

from common.utils.requests import url_to_buffer

logger = logging.getLogger(__name__)


@memoize()
def save_tmp_file_from_url(media_url: str) -> Tuple[str, bytes]:
    content, _ = url_to_buffer(media_url)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".in") as tmp_in:
        tmp_in.write(content)
        return tmp_in.name, content
