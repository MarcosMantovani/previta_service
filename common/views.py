import base64, json, hmac, hashlib, time, urllib.parse
from botocore.exceptions import ClientError
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.conf import settings
from django.views.decorators.http import require_http_methods
from storages.backends.s3boto3 import S3Boto3Storage


def _b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _verify(token: str, secret: str):
    body_b64, sig_b64 = token.split(".", 1)
    body = _b64url_decode(body_b64)
    sig = _b64url_decode(sig_b64)
    if not hmac.compare_digest(
        sig, hmac.new(secret.encode(), body, hashlib.sha256).digest()
    ):
        raise ValueError("bad sig")
    data = json.loads(body)
    if data.get("exp", 0) < time.time():
        raise ValueError("expired")
    return data


@require_http_methods(["GET", "HEAD"])
def media_proxy(request, token, path):
    try:
        data = _verify(token, settings.MEDIA_PROXY_SECRET)
    except ValueError:
        raise Http404("Invalid token")

    if request.method == "HEAD":
        # Re-encaminha HEAD para o Wasabi e devolve só os headers
        storage = S3Boto3Storage()
        try:
            obj = storage.connection.meta.client.head_object(
                Bucket=storage.bucket_name, Key=path
            )
        except ClientError:
            raise Http404("not found")

        resp = HttpResponse(status=200)
        resp["Content-Type"] = obj["ContentType"]
        resp["Content-Length"] = str(obj["ContentLength"])
        resp["Cache-Control"] = obj.get("CacheControl", "max-age=3600")
        return resp

    # GET → redireciona pro link assinado
    return HttpResponseRedirect(data["g"])
