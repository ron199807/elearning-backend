"""
URL configuration for elearning_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from .swagger import schema_view
from registration_app.views import LoginView, LogoutView
from courses_app.views import CourseEnrollmentView, CourseRetrieveUpdateDestroyView, CourseListCreateView

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('api/user/', include('user_app.urls')),
    path('registration/', include('registration_app.urls')),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('courses/', include('courses_app.urls')),
    path('courses/<int:pk>/', CourseRetrieveUpdateDestroyView.as_view(), name='course-detail'),
    path('enroll/', CourseEnrollmentView.as_view(), name='course-enrollment'),
    path('courses/', CourseListCreateView.as_view(), name='course-list-create'),
    # path('api/payment/', include('payment_app.urls')),

    # Swagger URLs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]


