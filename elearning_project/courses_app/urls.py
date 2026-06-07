from django.urls import path
from . import views
from .views import (
    CategoryListCreateView, CategoryRetrieveUpdateDestroyView,
    CourseListCreateView, CourseRetrieveUpdateDestroyView,
    CourseModuleCreateView, LessonCreateView, CourseMaterialCreateView,
    CourseEnrollmentView, CheckCourseAccessView, CourseContentListView,
    CourseSearchView,
    LessonRetrieveUpdateDestroyView,
    CourseModuleRetrieveUpdateDestroyView,
    MarkLessonComplete, CourseProgressCreateView, EnrollmentProgressView, MarkCourseCompleteView, CertificateListView, CertificateCreateView, CertificateDetailView, VerifyCertificateView, CertificateByEnrollmentView, LessonVideoListCreateView,
    LessonVideoDetailView,
    LessonVideoReorderView,
    LessonVideoStreamView,
    get_certificate_by_course

)

urlpatterns = [
    # Categories
    path('categories/', CategoryListCreateView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDestroyView.as_view(), name='category-detail'),
    
    # Courses
    path('courses/', CourseListCreateView.as_view(), name='course-list'),
    path('courses/<int:pk>/', CourseRetrieveUpdateDestroyView.as_view(), name='course-detail'),
    path('courses/search/', CourseSearchView.as_view(), name='course-search'),
    path('courses/list/', views.CourseListView.as_view(), name='course-list'),
    path('courses/<int:pk>/detail/', views.CourseDetailView.as_view(), name='course-detail'),
    path('courses/create/', views.CourseCreateView.as_view(), name='course-create'),

    # Course Modules
    path('courses/<int:course_id>/modules/', CourseModuleCreateView.as_view(), name='module-list'),
    path('modules/<int:pk>/', CourseModuleRetrieveUpdateDestroyView.as_view(), name='module-detail'),
    path('courses/<int:course_id>/complete/', MarkCourseCompleteView.as_view(), name='mark-course-complete'),
    
    # Lessons
    path('modules/<int:module_id>/lessons/', LessonCreateView.as_view(), name='lesson-list'),
    path('lessons/', views.LessonListView.as_view(), name='lesson-list-all'),
    path('lessons/<int:pk>/', LessonRetrieveUpdateDestroyView.as_view(), name='lesson-detail'),
    path('lessons/<str:slug>/', views.LessonBySlugView.as_view(), name='lesson-detail-by-slug'),
    path('lessons/<int:lesson_id>/reorder/', views.LessonReorderView.as_view(), name='lesson-reorder'), 
    
    # Course Materials
    path('lessons/<int:lesson_id>/materials/', CourseMaterialCreateView.as_view(), name='material-list'),
    
    # Enrollment
    path('enrollments/', views.EnrollmentListView.as_view(), name='enrollment-list'),
    path('courses/<int:course_id>/enroll/', CourseEnrollmentView.as_view(), name='course-enroll'),
    path('courses/<int:course_id>/check-access/', CheckCourseAccessView.as_view(), name='check-access'),
    path('courses/<int:course_id>/content/', CourseContentListView.as_view(), name='course-content'),
     path('enrollments/<int:pk>/', views.EnrollmentDetailView.as_view(), name='enrollment-detail'),
    path('enrollments/<int:enrollment_id>/complete/', views.CompleteEnrollmentView.as_view(), name='enrollment-complete'),

     # Progress URLs
    path('progress/', views.CourseProgressListView.as_view(), name='progress-list'),
     path('lessons/<int:lesson_id>/complete/', views.MarkLessonComplete.as_view(), name='mark-lesson-complete'), 
    path('lessons/<int:lesson_id>/mark-incomplete/', views.MarkLessonIncompleteView.as_view(), name='mark-lesson-incomplete'),
    path('my-progress/', views.UserCourseProgressView.as_view(), name='user-progress'),
    
    # User course management
    path('my-courses/', views.MyCoursesView.as_view(), name='my-courses'),
    path('teaching-courses/', views.TeachingCoursesView.as_view(), name='teaching-courses'),
    
    # Course material management
    path('materials/<int:pk>/', views.CourseMaterialRetrieveUpdateDestroyView.as_view(), name='material-detail'),

    # Course progress endpoints
    path('courses/<int:course_id>/progress/', views.CourseProgressView.as_view(), name='course-progress'),
    path('enrollments/<int:enrollment_id>/progress/', views.EnrollmentProgressView.as_view(), name='enrollment-progress'),


        # Video streaming URLs
    path('lessons/<int:lesson_id>/stream/', views.VideoStreamView.as_view(), name='lesson-video-stream'),
    path('lessons/<int:lesson_id>/video-info/', views.LessonVideoInfoView.as_view(), name='lesson-video-info'),
    
    # Alternative URL pattern for the React component
    path('lessons/<int:lesson_id>/video/', views.VideoStreamView.as_view(), name='lesson-video'),

    # Certificate URLs
    path('certificates/', CertificateListView.as_view(), name='user-certificates'),
    path('certificates/create/<int:enrollment_id>/', CertificateCreateView.as_view(), name='create-certificate'),
    path('certificates/<str:certificate_id>/', CertificateDetailView.as_view(), name='certificate-detail'),
    path('certificates/verify/<str:verification_token>/', VerifyCertificateView.as_view(), name='verify-certificate'),
    path('certificates/enrollment/<int:enrollment_id>/', CertificateByEnrollmentView.as_view(), name='certificate-by-enrollment'),
    path('certificates/course/<int:course_id>/', get_certificate_by_course, name='certificate-by-course'),

        # Lesson Videos URLs
    path('lessons/<int:lesson_id>/videos/', LessonVideoListCreateView.as_view(), name='lesson-videos'),
    path('lesson-videos/<int:pk>/', LessonVideoDetailView.as_view(), name='lesson-video-detail'),
    path('lessons/<int:lesson_id>/videos/reorder/', LessonVideoReorderView.as_view(), name='lesson-videos-reorder'),
    path('lesson-videos/<int:video_id>/stream/', LessonVideoStreamView.as_view(), name='lesson-video-stream'),

    # File upload endpoints
    path('upload/video/', views.upload_video, name='upload-video'),
    path('upload/thumbnail/', views.upload_thumbnail, name='upload-thumbnail'),
    path('upload/material/', views.upload_material, name='upload-material'),
    path('upload/files/', views.delete_file, name='delete-file'),
]