"""
Root URL configuration.

API is versioned under /api/v1/ for future-proofing.
Schema endpoints are only exposed in DEBUG mode.
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.users.urls.auth_urls")),
    path("api/v1/users/", include("apps.users.urls.user_urls")),
    path("api/v1/finance/", include("apps.finance.urls")),
    # OpenAPI schema + Swagger UI (great for internship demo/review)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
