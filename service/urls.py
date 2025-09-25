from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path, re_path
from django.views import defaults as default_views
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from common.views import media_proxy


def admin_redirect(request):
    return redirect("/admin/")


def avoid_dashboard(request):

    if not request.user.is_authenticated:
        return redirect("admin:login")

    return admin.site.index(request)


urlpatterns = [
    re_path(r"^$", admin_redirect),
    re_path(r"^admin/$", avoid_dashboard),
    path("admin/", admin.site.urls),
    path("_autogfk/", include("autogfk.urls")),
    path("martor/", include("martor.urls")),
    path("api/auth/", include("authentication.urls", namespace="authentication")),
    path("api/users/", include("users.urls", namespace="users")),
    path("api/residents/", include("residents.urls", namespace="residents")),
    path("api/medications/", include("medications.urls", namespace="medications")),
    path("api/appointments/", include("appointments.urls", namespace="appointments")),
    # API Schema Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    re_path(
        r"^media-proxy/(?P<token>[^/]+)/(?P<path>.+)$", media_proxy, name="media_proxy"
    ),
]


if settings.DEBUG:
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
