from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.conf import settings
from django.conf.urls.static import static

# Import CSRF views from courses_app
from courses_app.views import CSRFTokenView, get_csrf_token, test_csrf

# Swagger schema view
schema_view = get_schema_view(
    openapi.Info(
        title="E-Learning Platform API",
        default_version='v1',
        description="API for managing courses, users, and enrollments.",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Debug CSRF endpoint
@csrf_exempt
def debug_csrf(request):
    """Debug endpoint to check CSRF configuration"""
    csrf_token = get_token(request)
    
    return JsonResponse({
        'csrf_token_available': bool(csrf_token),
        'csrf_token': csrf_token,
        'cookies': dict(request.COOKIES),
        'headers': dict(request.headers),
        'is_secure': request.is_secure(),
        'scheme': request.scheme,
        'method': request.method,
        'path': request.path,
        'host': request.get_host(),
    })

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('registration_app.urls')),
    path('api/', include('courses_app.urls')),

    # API documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # CSRF endpoints for frontend - THESE MUST BE BEFORE OTHER API ENDPOINTS
    path('api/csrf/', get_csrf_token, name='csrf_token'),
    path('api/csrf-token/', CSRFTokenView.as_view(), name='csrf_token_class'),
    path('api/test-csrf/', test_csrf, name='test_csrf'),
    path('api/debug-csrf/', debug_csrf, name='debug_csrf'),
]

# Handle media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)