from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="E-Learning API",
        default_version='v1',
        description="API documentation for the E-Learning platform",
    ),
    public=True,
    permission_classes=[AllowAny],
)
