# courses_app/urls.py
from django.urls import path
from .views import (
    CategoryListCreateView,
    CategoryRetrieveUpdateDestroyView,
    CourseListCreateView,
    CourseRetrieveUpdateDestroyView,
    CourseEnrollmentView,
    student_dashboard,
)

urlpatterns = [
    # Category URLs
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDestroyView.as_view(), name='category-retrieve-update-destroy'),

    # Course URLs
    path('courses/', CourseListCreateView.as_view(), name='course-list-create'),
    path('courses/<int:pk>/', CourseRetrieveUpdateDestroyView.as_view(), name='course-retrieve-update-destroy'),

    # Enrollment URL
    path('courses/enroll/', CourseEnrollmentView.as_view(), name='course-enrollment'),

    # Student Dashboard URL
    path('student-dashboard/', student_dashboard, name='student-dashboard'),
]