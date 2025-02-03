from django.urls import path
from .views import CourseListCreateView, CourseEnrollmentView, CourseRetrieveUpdateDestroyView, CategoryListCreateView, CategoryRetrieveUpdateDestroyView

urlpatterns = [
    path('courses/', CourseListCreateView.as_view(), name='course-list-create'),
    path('courses/<int:pk>/', CourseRetrieveUpdateDestroyView.as_view(), name='course-detail'),
    path('enroll/', CourseEnrollmentView.as_view(), name='course-enrollment'),

     path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDestroyView.as_view(), name='category-retrieve-update-destroy'),
]
