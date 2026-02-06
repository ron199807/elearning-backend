# elearning_project/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.middleware.csrf import get_token

@csrf_exempt
def debug_csrf(request):
    """Debug endpoint to check CSRF configuration"""
    csrf_token = get_token(request) if hasattr(request, 'csrf_token') else None
    
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
        'meta_keys': list(request.META.keys()),
    })

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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('registration_app.urls')),  # Include registration_app URLs
    path('api/', include('courses_app.urls')),      # Include courses_app URLs

    # api documentation urls
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# to handle images
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)