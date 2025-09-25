import re
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, URLValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_ipv6_address
from localflavor.br.forms import BRCNPJField, BRCPFField
from urllib.parse import urlsplit


@deconstructible
class MaxFileSizeValidator(MaxValueValidator):
    message = _(
        "Tamanho do arquivo %(show_value)d excede o tamanho máximo de %(limit_value)d Mb."
    )

    def clean(self, filefield) -> float:
        return filefield.file.size / 1024 / 1024


def validate_cpf(value):
    try:
        BRCPFField().clean(value)
    except ValidationError as e:
        raise ValidationError("Formato de CPF inválido") from e


def validate_cnpj(value):
    try:
        BRCNPJField().clean(value)
    except ValidationError as e:
        raise ValidationError("Formato de CNPJ inválido") from e


def validate_cpf_cnpj(value):
    value = value.replace(".", "").replace("-", "").replace("/", "")

    if len(value) == 11:
        validate_cpf(value)
    elif len(value) == 14:
        validate_cnpj(value)
    else:
        raise ValidationError("Formato de CPF/CNPJ inválido")


@deconstructible
class RelaxedURLValidator(URLValidator):
    """
    Igual ao URLValidator do Django, mas aceita hostnames sem TLD
    (ex.: 'previta-evolution'), além de 'localhost'.
    Mantém validação de IPv4/IPv6 e porta opcional.
    """

    # Reaproveita os padrões da base:
    ipv4_re = URLValidator.ipv4_re
    ipv6_re = URLValidator.ipv6_re

    # Um label DNS: [a-z0-9] com hifens no meio, até 63 chars
    _label = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    # Hostname relaxado: permite apenas 1 label (sem TLD) ou múltiplos labels.
    relaxed_host_re = "(" + _label + r"(?:\." + _label + r")*" + "|localhost)"

    def __init__(self, schemes=None, **kwargs):
        super().__init__(schemes=schemes, **kwargs)
        # Recompila o REGEX principal usando o host relaxado.
        self.regex = re.compile(
            r"^(?:[a-z0-9.+-]*)://"  # scheme
            r"(?:[^\s:@/]+(?::[^\s:@/]*)?@)?"  # user:pass@
            r"(?:"
            + self.ipv4_re
            + "|"
            + self.ipv6_re
            + "|"
            + self.relaxed_host_re
            + ")"
            r"(?::[0-9]{1,5})?"  # <-- porta opcional
            r"(?:[/?#][^\s]*)?"  # path/query/fragment
            r"\Z",
            re.IGNORECASE,
        )

    def __call__(self, value):
        # Mantém as mesmas checagens da classe base (scheme, ipv6 etc.)
        if not isinstance(value, str) or len(value) > self.max_length:
            raise ValidationError(self.message, code=self.code, params={"value": value})
        if self.unsafe_chars.intersection(value):
            raise ValidationError(self.message, code=self.code, params={"value": value})
        scheme = value.split("://")[0].lower()
        if scheme not in self.schemes:
            raise ValidationError(self.message, code=self.code, params={"value": value})
        try:
            splitted_url = urlsplit(value)
        except ValueError:
            raise ValidationError(self.message, code=self.code, params={"value": value})

        # Aplica nosso regex recompilado
        if not self.regex.match(value):
            raise ValidationError(self.message, code=self.code, params={"value": value})

        # Checagem extra de IPv6 (igual à base)
        host_match = re.search(r"^\[(.+)\](?::[0-9]{1,5})?$", splitted_url.netloc)
        if host_match:
            try:
                validate_ipv6_address(host_match[1])
            except ValidationError:
                raise ValidationError(
                    self.message, code=self.code, params={"value": value}
                )
