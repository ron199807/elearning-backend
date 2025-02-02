from django.urls import path
from .views import CourseListCreateView, CourseEnrollmentView, CourseRetrieveUpdateDestroyView

urlpatterns = [
    path('courses/', CourseListCreateView.as_view(), name='course-list-create'),
    path('courses/<int:pk>/', CourseRetrieveUpdateDestroyView.as_view(), name='course-detail'),
    path('enroll/', CourseEnrollmentView.as_view(), name='course-enrollment'),
]
