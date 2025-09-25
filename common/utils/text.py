import unicodedata
import logging
from Levenshtein import distance as levenshtein_distance
from unidecode import unidecode
from memoize import memoize

logger = logging.getLogger(__name__)


@memoize()
def sanitize_string(string, remove_diacritics=True, uppercase=True):
    if not string:
        return None

    if not isinstance(string, str):
        string = str(string)

    if remove_diacritics:
        string = unidecode(string)

    if uppercase:
        string = string.upper()

    return string.strip()


@memoize()
def estimate_strings_similarity(string1, string2):
    """
    Estima a similaridade entre duas strings.

    Args:
        string1 (str): A primeira string
        string2 (str): A segunda string

    Returns:
        float: O grau de similaridade entre as duas strings
    """

    # Remove espaços e caracteres especiais
    string1 = (
        string1.lower()
        .replace(" ", "")
        .replace(".", "")
        .replace(",", "")
        .replace("!", "")
        .replace("?", "")
    )
    string2 = (
        string2.lower()
        .replace(" ", "")
        .replace(".", "")
        .replace(",", "")
        .replace("!", "")
        .replace("?", "")
    )

    # Calcula a distância de Levenshtein
    distance = levenshtein_distance(string1, string2)

    # Calcula a similaridade
    similarity = 1 - (distance / max(len(string1), len(string2)))

    return similarity


@memoize()
def replace_accents_characters(str):
    """
    Function to replace accented characters with their corresponding non-accented ascii characters
    """
    return unicodedata.normalize("NFKD", str).encode("ascii", "ignore").decode("utf-8")


def normalize_mathematical_text(text):
    # Usamos NFKC ao invés de NFKD para manter os acentos
    # NFKC faz a composição dos caracteres, mantendo acentos
    normalized = unicodedata.normalize("NFKC", text)

    # Removemos apenas caracteres de controle indesejados,
    # mas mantemos espaços (Zs), quebras de linha (Cc - \n, \r) e tabs (Cc - \t)
    result = "".join(
        c
        for c in normalized
        if not unicodedata.category(c).startswith("C") or c in [" ", "\n", "\r", "\t"]
    )

    return result


@memoize()
def format_phone_number(phone_number: str) -> str:
    """
    Formats a phone number to the format +55 (11) 99999-9999
    or +55 (11) 9999-9999 for short numbers
    """

    if len(phone_number) == 13:  # 5511957820329
        return f"+55 ({phone_number[2:4]}) {phone_number[4:9]}-{phone_number[9:]}"
    elif len(phone_number) == 12:  # 559991143517
        return f"+55 ({phone_number[2:4]}) {phone_number[4:8]}-{phone_number[8:]}"
    else:
        return phone_number
