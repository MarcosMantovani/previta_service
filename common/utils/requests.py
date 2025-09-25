import time
import logging
import requests
from functools import wraps
from requests.exceptions import ConnectionError
from memoize import memoize

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries=3, delay=3):
    """
    Decorator para tentar executar uma função novamente se houver erro de conexão.

    Args:
        max_retries: Número máximo de tentativas
        delay: Delay entre tentativas (em segundos)

    Returns:
        Decorator para tentar executar uma função novamente se houver erro de conexão.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except ConnectionError as e:
                    if attempt == max_retries - 1:  # Last attempt
                        logger.error(f"Failed after {max_retries} attempts: {str(e)}")
                        raise  # Re-raise the last exception
                    logger.warning(
                        f"Connection error on attempt {attempt + 1}: {str(e)}. Retrying..."
                    )
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
            return None

        return wrapper

    return decorator


@memoize()
def url_to_buffer(url: str, timeout: int = 30) -> tuple[bytes, dict]:
    """
    Baixa o conteúdo de um URL e retorna o conteúdo e os headers.

    Args:
        url: URL do arquivo

    Returns:
        tuple[bytes, dict]: Conteúdo e headers do arquivo
    """
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content, response.headers
