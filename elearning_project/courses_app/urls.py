from django.urls import path
from .views import (
    CategoryListCreateView,
    CategoryRetrieveUpdateDestroyView,
    CourseListCreateView,
    CourseSearchView,
    CheckCourseAccessView,
    CourseRetrieveUpdateDestroyView,
    CourseEnrollmentView,
    student_dashboard,
)

urlpatterns = [
    # Category URLs
     path('categories/', CategoryListCreateView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDestroyView.as_view(), name='category-retrieve-update-destroy'),

    # Course URLs
    path('courses/', CourseListCreateView.as_view(), name='course-list-create'),
    path('courses/<int:pk>/', CourseRetrieveUpdateDestroyView.as_view(), name='course-retrieve-update-destroy'),
    path('courses/<int:course_id>/check-access/', CheckCourseAccessView.as_view(), name='check-course-access'),
    path('courses/search/', CourseSearchView.as_view(), name='course-search'),

    # Enrollment URL
    path('courses/enroll/', CourseEnrollmentView.as_view(), name='course-enrollment'),

    # Student Dashboard URL
    path('student-dashboard/', student_dashboard, name='student-dashboard'),
]