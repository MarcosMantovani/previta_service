import mimetypes
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

# garante que ".opus" seja reconhecido
mimetypes.add_type("audio/opus", ".opus", strict=False)


class ConditionalS3CacheStorage(S3Boto3Storage):
    """
    1. Salva objetos com Content-Type/Cache-Control corretos
    2. Devolve um único URL (proxy) que serve HEAD e GET
    """

    def url(self, name, *a, **kw):
        return f"https://media.previta.com.br/{name}"

    # ---------- Metadados no upload ----------
    def get_object_parameters(self, name):
        params = super().get_object_parameters(name)

        # Cache-Control
        if name.startswith("uploads/media/contacts"):
            params["CacheControl"] = "max-age=604800, public"  # 7 dias
        elif name.startswith("uploads/media"):
            params["CacheControl"] = "max-age=31536000, immutable, public"

        # Content-Type
        lower = name.lower()
        if lower.endswith(".opus"):
            params["ContentType"] = "audio/ogg; codecs=opus"
        elif lower.endswith(".mp3"):
            params["ContentType"] = "audio/mpeg"
        elif lower.endswith((".mp4", ".m4v")):
            params["ContentType"] = "video/mp4"
        elif lower.endswith(".m4a"):
            params["ContentType"] = "audio/mp4"

        return params
