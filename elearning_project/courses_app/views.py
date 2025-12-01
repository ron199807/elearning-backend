from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from .models import Course, Category, CourseModule, Lesson, CourseMaterial, Enrollment, CourseProgress
from django.http import StreamingHttpResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from wsgiref.util import FileWrapper
import os
from django.conf import settings
from django.utils.encoding import smart_str
from .serializers import (
    CourseSerializer, CategorySerializer, CourseModuleSerializer,
    LessonSerializer, CourseMaterialSerializer, EnrollmentSerializer, CourseProgressSerializer, CourseDetailSerializer, CourseCreateSerializer, CourseListSerializer
)
from registration_app.permissions import IsInstructor, IsAdminUser, IsStudent, CanEnrollInCourse
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from django.http import JsonResponse, Http404
from django.utils import timezone
from registration_app.permissions import IsInstructor, IsStudent, IsAdminUser, CanEnrollInCourse
from django.db.models import Q

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return super().get_permissions()

class CategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class CourseListCreateView(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(instructor=self.request.user)
        else:
            raise serializers.ValidationError("You must be logged in to create a course.")
        

    # OVERRIDE THIS METHOD - This is the key fix!
    def create(self, request, *args, **kwargs):
        print("📝 Course creation request received")
        print(f"📦 Request data: {request.data}")
        print(f"👤 User: {request.user.username}")
        
        # Call the serializer and create the course
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        print(f"✅ Course created with ID: {serializer.instance.id}")
        
        # Return the created course data, not the list
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class CourseRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsInstructor()]
        return super().get_permissions()

class CourseModuleCreateView(generics.ListCreateAPIView):
    serializer_class = CourseModuleSerializer
    permission_classes = [IsAuthenticated] # base permission for all authenticated users

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        # For POST requests, require instructor role
        elif self.request.method == 'POST':
            return [IsAuthenticated(), IsInstructor()]
        return super().get_permissions()

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return CourseModule.objects.filter(course_id=course_id)

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs['course_id'])
        if course.instructor != self.request.user:
            raise PermissionDenied("You are not the instructor of this course.")
        serializer.save(course=course)

class LessonCreateView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        elif self.request.method == 'POST':
            return [IsAuthenticated(), IsInstructor()]
        return super().get_permissions()

    def get_queryset(self):
        module_id = self.kwargs['module_id']
        return Lesson.objects.filter(module_id=module_id)

    def perform_create(self, serializer):
        module = get_object_or_404(CourseModule, id=self.kwargs['module_id'])
        if module.course.instructor != self.request.user:
            raise PermissionDenied("You are not the instructor of this course.")
        serializer.save(module=module)

class CourseMaterialCreateView(generics.ListCreateAPIView):
    serializer_class = CourseMaterialSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        elif self.request.method == 'POST':
            return [IsAuthenticated(), IsInstructor()]
        return super().get_permissions()

    def get_queryset(self):
        lesson_id = self.kwargs['lesson_id']
        return CourseMaterial.objects.filter(lesson_id=lesson_id)

    def perform_create(self, serializer):
        lesson = get_object_or_404(Lesson, id=self.kwargs['lesson_id'])
        if lesson.module.course.instructor != self.request.user:
            raise PermissionDenied("You are not the instructor of this course.")
        serializer.save(lesson=lesson)

class CourseEnrollmentView(APIView):
    permission_classes = [CanEnrollInCourse]  # Any authenticated user can enroll

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        
        # Check if already enrolled
        if Enrollment.objects.filter(user=request.user, course=course).exists():
            return Response(
                {"error": "You are already enrolled in this course"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # For free courses, enroll directly
        if not course.is_paid:
            enrollment = Enrollment.objects.create(
                user=request.user,
                course=course,
                payment_status='free'
            )
            course.students.add(request.user)
            return Response(
                {"message": "Enrolled successfully in free course"},
                status=status.HTTP_201_CREATED
            )
        
        # For paid courses, create a pending enrollment
        enrollment = Enrollment.objects.create(
            user=request.user,
            course=course,
            payment_status='pending'
        )
        # Here you would typically integrate with a payment gateway
        # For now, we'll just return the enrollment details
        return Response(
            {
                "message": "Payment required for enrollment",
                "enrollment_id": enrollment.id,
                "course_price": course.price
            },
            status=status.HTTP_200_OK
        )

class CheckCourseAccessView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {"error": "Course not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # For free courses, all authenticated users have access
        if not course.is_paid:
            return Response({
                "has_access": True,
                "message": "This is a free course. You have full access.",
                "is_free": True
            })
            
        # For paid courses, check enrollment
        enrollment = Enrollment.objects.filter(
            user=request.user, 
            course=course,
            payment_status='completed'
        ).first()
        
        if enrollment:
            return Response({
                "has_access": True,
                "message": "You have access to this paid course.",
                "enrollment_id": enrollment.id
            })
            
        return Response({
            "has_access": False,
            "message": "You need to enroll and pay to access this course.",
            "price": str(course.price),
            "course_id": course.id
        })

class CourseContentListView(APIView):
    permission_classes = [IsAuthenticated]  # Only authenticated users can access content

    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)

        print(f"=== COURSE CONTENT DEBUG ===")
        print(f"User: {request.user.username}")
        print(f"Course: {course.title}")
        print(f"Course is_paid: {course.is_paid}")
        print(f"User in students: {request.user in course.students.all()}")
        print(f"============================")
        
        # For free courses, all authenticated users can view content
        if not course.is_paid:
            modules = CourseModule.objects.filter(course=course).prefetch_related(
                'lessons', 'lessons__materials'
            )
            serializer = CourseModuleSerializer(modules, many=True, context={'request': request})
            return Response(serializer.data)
        
        # For paid courses, check enrollment
        enrollment = Enrollment.objects.filter(
            user=request.user, 
            course=course,
            payment_status='completed'
        ).first()
        
        if enrollment:
            modules = CourseModule.objects.filter(course=course).prefetch_related(
                'lessons', 'lessons__materials'
            )
            serializer = CourseModuleSerializer(modules, many=True, context={'request': request})
            return Response(serializer.data)
        
        return Response(
            {"error": "You don't have access to this course content. Please enroll and complete payment."},
            status=status.HTTP_403_FORBIDDEN
        )

class CourseSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get('query', '')
        courses = Course.objects.filter(title__icontains=query)
        serializer = CourseSerializer(courses, many=True, context={'request': request})
        return Response(serializer.data)

class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated(), IsInstructor()]
        return super().get_permissions()

    def get_queryset(self):
        # For instructors, only show lessons from their courses
        if self.request.user.role == 'instructor':
            return Lesson.objects.filter(module__course__instructor=self.request.user)
        # For students, show lessons from enrolled courses
        elif self.request.user.role == 'student':
            return Lesson.objects.filter(module__course__students=self.request.user)
        # Fallback for other roles
        return Lesson.objects.all()
    
    def get_object(self):
    # Override to provide better error messages
        try:
            lesson = super().get_object()
            # Additional permission check for instructors
            if (self.request.user.role == 'instructor' and 
                lesson.module.course.instructor != self.request.user):
                raise PermissionDenied("You are not the instructor of this course.")
            return lesson
        except Lesson.DoesNotExist:
            raise Http404("Lesson not found or you don't have permission to access it.")
        
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Use partial=True for PATCH requests
        if request.method == 'PATCH':
            partial = True
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)

class CourseModuleRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CourseModule.objects.all()
    serializer_class = CourseModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated(), IsInstructor()]
        return super().get_permissions()

    def get_queryset(self):
        # Ensure users can only access modules from their courses
        if self.request.user.role == 'instructor':
            return CourseModule.objects.filter(course__instructor=self.request.user)
        return CourseModule.objects.all()
    

class CourseListView(generics.ListAPIView):
    """List view for courses with minimal data"""
    queryset = Course.objects.filter(status='published', is_public=True)
    serializer_class = CourseListSerializer
    permission_classes = [AllowAny]
    filter_backends = []  # Add DjangoFilterBackend, SearchFilter if needed

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class CourseDetailView(generics.RetrieveAPIView):
    """Detail view for courses with full data"""
    queryset = Course.objects.all()
    serializer_class = CourseDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CourseDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        # For non-authenticated users, only show published courses
        if not self.request.user.is_authenticated:
            return Course.objects.filter(status='published', is_public=True)
        
        # For authenticated users
        if self.request.user.is_staff:
            return Course.objects.all()
        
        # Instructors can see their own courses + published courses
        if hasattr(self.request.user, 'is_instructor') and self.request.user.is_instructor:
            return Course.objects.filter(
                Q(instructor=self.request.user) | 
                Q(status='published', is_public=True)
            )
        
        # Regular users can only see published public courses
        return Course.objects.filter(status='published', is_public=True)

class CourseCreateView(generics.CreateAPIView):
    """Create view for courses with validation"""
    queryset = Course.objects.all()
    serializer_class = CourseCreateSerializer
    permission_classes = [IsAuthenticated, IsInstructor]

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

class EnrollmentListView(generics.ListAPIView):
    """List enrollments for the current user"""
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff:
            return Enrollment.objects.all().select_related('user', 'course')
        
        # Instructors can see enrollments in their courses
        if hasattr(user, 'is_instructor') and user.is_instructor:
            return Enrollment.objects.filter(
                course__instructor=user
            ).select_related('user', 'course')
        
        # Regular users can only see their own enrollments
        return Enrollment.objects.filter(user=user).select_related('user', 'course')

class EnrollmentCreateView(generics.CreateAPIView):
    """Create enrollment for a course"""
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, CanEnrollInCourse]

    def perform_create(self, serializer):
        course_id = self.kwargs.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        
        # Check if already enrolled
        if Enrollment.objects.filter(user=self.request.user, course=course).exists():
            raise serializers.ValidationError("You are already enrolled in this course.")
        
        # Check if enrollment is allowed
        if not course.allow_enrollment:
            raise serializers.ValidationError("Enrollment is not currently available for this course.")
        
        # Check if course is available
        if not course.is_available:
            raise serializers.ValidationError("This course is not available for enrollment.")
        
        # Handle payment status
        payment_status = 'paid'
        amount_paid = 0
        
        if course.is_paid and course.current_price > 0:
            payment_status = 'pending'
            amount_paid = course.current_price
        
        serializer.save(
            user=self.request.user,
            course=course,
            payment_status=payment_status,
            amount_paid=amount_paid
        )

class EnrollmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an enrollment"""
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff:
            return Enrollment.objects.all()
        
        if hasattr(user, 'is_instructor') and user.is_instructor:
            return Enrollment.objects.filter(course__instructor=user)
        
        return Enrollment.objects.filter(user=user)

class CourseProgressListView(generics.ListAPIView):
    """List course progress for the current user"""
    serializer_class = CourseProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff:
            return CourseProgress.objects.all()
        
        return CourseProgress.objects.filter(enrollment__user=user)

class CourseProgressCreateView(generics.CreateAPIView):
    """Create or update course progress"""
    serializer_class = CourseProgressSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        lesson_id = self.kwargs.get('lesson_id')
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Get user's enrollment in this course
        enrollment = Enrollment.objects.filter(
            user=self.request.user,
            course=lesson.module.course
        ).first()
        
        if not enrollment:
            raise PermissionDenied("You are not enrolled in this course.")
        
        # Update or create progress
        progress, created = CourseProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={
                'completed': True, 
                'completed_at': timezone.now(),
                'last_accessed': timezone.now()
            }
        )
        
        if not created:
            progress.completed = True
            progress.completed_at = timezone.now()
            progress.last_accessed = timezone.now()
            progress.save()
        
        # Check if course is completed
        self._check_course_completion(enrollment)

    def _check_course_completion(self, enrollment):
        """Check if all lessons are completed and update enrollment status"""
        total_lessons = Lesson.objects.filter(module__course=enrollment.course).count()
        completed_lessons = CourseProgress.objects.filter(
            enrollment=enrollment,
            completed=True
        ).count()
        
        if total_lessons > 0 and completed_lessons == total_lessons:
            enrollment.completed = True
            enrollment.completed_at = timezone.now()
        else:
            enrollment.completed = False
            enrollment.completed_at = None
        
        enrollment.save()

class MarkLessonCompleteView(APIView):
    """Mark a lesson as completed"""
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Get user's enrollment
        enrollment = Enrollment.objects.filter(
            user=request.user,
            course=lesson.module.course
        ).first()
        
        if not enrollment:
            return Response(
                {"error": "You are not enrolled in this course."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create or update progress
        progress, created = CourseProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={'completed': True, 'completed_at': timezone.now()}
        )
        
        if not created and not progress.completed:
            progress.completed = True
            progress.completed_at = timezone.now()
            progress.save()
        
        serializer = CourseProgressSerializer(progress, context={'request': request})
        return Response(serializer.data)

class MarkLessonIncompleteView(APIView):
    """Mark a lesson as incomplete"""
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        enrollment = Enrollment.objects.filter(
            user=request.user,
            course=lesson.module.course
        ).first()
        
        if not enrollment:
            return Response(
                {"error": "You are not enrolled in this course."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        progress = CourseProgress.objects.filter(
            enrollment=enrollment,
            lesson=lesson
        ).first()
        
        if progress:
            progress.completed = False
            progress.completed_at = None
            progress.save()
        
        if progress:
            serializer = CourseProgressSerializer(progress, context={'request': request})
            return Response(serializer.data)
        return Response({"message": "Lesson marked as incomplete."})

class UserCourseProgressView(APIView):
    """Get overall progress for all user's enrolled courses"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        enrollments = Enrollment.objects.filter(user=request.user)
        progress_data = []
        
        for enrollment in enrollments:
            total_lessons = Lesson.objects.filter(module__course=enrollment.course).count()
            completed_lessons = CourseProgress.objects.filter(
                enrollment=enrollment,
                completed=True
            ).count()
            
            progress_percentage = 0
            if total_lessons > 0:
                progress_percentage = int((completed_lessons / total_lessons) * 100)
            
            progress_data.append({
                'course_id': enrollment.course.id,
                'course_title': enrollment.course.title,
                'enrollment_id': enrollment.id,
                'total_lessons': total_lessons,
                'completed_lessons': completed_lessons,
                'progress_percentage': progress_percentage,
                'completed': enrollment.completed
            })
        
        return Response(progress_data)

class MyCoursesView(generics.ListAPIView):
    """Get courses where user is enrolled"""
    serializer_class = CourseListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        enrollments = Enrollment.objects.filter(user=self.request.user)
        course_ids = enrollments.values_list('course_id', flat=True)
        return Course.objects.filter(id__in=course_ids)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class TeachingCoursesView(generics.ListAPIView):
    """Get courses taught by the current user (for instructors)"""
    serializer_class = CourseListSerializer
    permission_classes = [IsAuthenticated, IsInstructor]

    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class CourseMaterialRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete course material"""
    queryset = CourseMaterial.objects.all()
    serializer_class = CourseMaterialSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated(), IsInstructor()]
        return super().get_permissions()

    def get_queryset(self):
        # Ensure instructors can only access materials from their courses
        if self.request.user.role == 'instructor':
            return CourseMaterial.objects.filter(lesson__module__course__instructor=self.request.user)
        return CourseMaterial.objects.all()

class CompleteEnrollmentView(APIView):
    """Manually mark enrollment as completed (for instructors)"""
    permission_classes = [IsAuthenticated, IsInstructor]

    def post(self, request, enrollment_id):
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        
        # Check if user is the course instructor
        if enrollment.course.instructor != request.user and not request.user.is_staff:
            return Response(
                {"error": "Only the course instructor can mark enrollments as complete."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        enrollment.completed = True
        enrollment.completed_at = timezone.now()
        enrollment.save()
        
        serializer = EnrollmentSerializer(enrollment, context={'request': request})
        return Response(serializer.data)

class MarkLessonComplete(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, lesson_id):
        try:
            lesson = get_object_or_404(Lesson, id=lesson_id)
            user = request.user
            
            # Get or create enrollment for this course
            enrollment, created = Enrollment.objects.get_or_create(
                user=user,
                course=lesson.module.course,
                defaults={
                    'payment_status': 'free' if not lesson.module.course.is_paid else 'pending'
                }
            )
            
            # Get or create course progress
            progress, created = CourseProgress.objects.get_or_create(
                enrollment=enrollment,
                lesson=lesson,
                defaults={
                    'completed': True,
                    'completed_at': timezone.now()
                }
            )
            
            if not progress.completed:
                progress.completed = True
                progress.completed_at = timezone.now()
                progress.save()
            
            # Check if course is completed
            self.check_course_completion(enrollment)
            
            return Response({
                'message': 'Lesson marked as completed',
                'progress': CourseProgressSerializer(progress).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def check_course_completion(self, enrollment):
        """Check if all lessons in the course are completed"""
        course = enrollment.course
        total_lessons = Lesson.objects.filter(module__course=course).count()
        completed_lessons = CourseProgress.objects.filter(
            enrollment=enrollment,
            completed=True
        ).count()
        
        if total_lessons > 0 and completed_lessons == total_lessons:
            enrollment.completed = True
            enrollment.completed_at = timezone.now()
            enrollment.save()

class CourseProgressView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        user = request.user
        
        try:
            enrollment = Enrollment.objects.get(user=user, course=course)
            progress_data = self.get_course_progress(enrollment)
            return Response(progress_data)
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'You are not enrolled in this course'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    def get_course_progress(self, enrollment):
        course = enrollment.course
        modules = course.modules.prefetch_related('lessons').all()
        total_lessons = Lesson.objects.filter(module__course=course).count()
        completed_lessons = CourseProgress.objects.filter(
            enrollment=enrollment,
            completed=True
        ).count()
        
        progress_percentage = 0
        if total_lessons > 0:
            progress_percentage = (completed_lessons / total_lessons) * 100
        
        module_progress = []
        for module in modules:
            module_lessons = module.lessons.count()
            completed_module_lessons = CourseProgress.objects.filter(
                enrollment=enrollment,
                lesson__module=module,
                completed=True
            ).count()
            
            module_progress.append({
                'module_id': module.id,
                'module_title': module.title,
                'completed_lessons': completed_module_lessons,
                'total_lessons': module_lessons,
                'progress': (completed_module_lessons / module_lessons * 100) if module_lessons > 0 else 0
            })
        
        return {
            'course_id': course.id,
            'course_title': course.title,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percentage': progress_percentage,
            'is_completed': enrollment.completed,
            'module_progress': module_progress
        }

class EnrollmentProgressView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, enrollment_id):
        enrollment = get_object_or_404(Enrollment, id=enrollment_id, user=request.user)
        progress_data = CourseProgressView().get_course_progress(enrollment)
        return Response(progress_data)


class LessonListView(generics.ListAPIView):
    """Get all lessons"""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

class LessonBySlugView(generics.RetrieveUpdateDestroyAPIView):
    """Get lesson by slug/title"""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    lookup_field = 'title'  # or 'slug' if you have a slug field
    
    def get_object(self):
        title = self.kwargs.get('slug')
        return get_object_or_404(Lesson, title=title)

class LessonReorderView(generics.UpdateAPIView):
    """Reorder lessons within a module"""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    
    def patch(self, request, *args, **kwargs):
        lesson_id = kwargs.get('lesson_id')
        new_order = request.data.get('order')
        
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            lesson.order = new_order
            lesson.save()
            return Response(LessonSerializer(lesson).data)
        except Lesson.DoesNotExist:
            return Response(
                {'error': 'Lesson not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class VideoStreamView(APIView):
    """Stream video files securely with authentication"""
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Check if user has access to this lesson
        if not self._has_access(request.user, lesson):
            return Response(
                {"error": "You don't have access to this video"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check if lesson has a video file
        if not lesson.video_file:
            return Response(
                {"error": "No video file available for this lesson"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get the video file path
        video_path = lesson.video_file.path
        
        # Stream the video file
        try:
            response = self._stream_video(request, video_path, lesson.video_file.name)
            return response
        except Exception as e:
            return Response(
                {"error": f"Error streaming video: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _has_access(self, user, lesson):
        """Check if user has access to the lesson"""
        # For free courses, all authenticated users have access
        if not lesson.module.course.is_paid:
            return True
        
        # For paid courses, check enrollment
        enrollment = Enrollment.objects.filter(
            user=user,
            course=lesson.module.course,
            payment_status__in=['completed', 'free']
        ).first()
        
        return enrollment is not None

    def _stream_video(self, request, file_path, filename):
        """Stream video file with proper headers"""
        file_size = os.path.getsize(file_path)
        range_header = request.META.get('HTTP_RANGE', '').strip()
        range_match = range_header.match(r'bytes=(\d+)-(\d+)?') if range_header else None
        
        if range_match:
            start_byte = int(range_match.group(1))
            end_byte = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            
            if end_byte >= file_size:
                end_byte = file_size - 1
            
            length = end_byte - start_byte + 1
            
            with open(file_path, 'rb') as f:
                f.seek(start_byte)
                data = f.read(length)
            
            response = HttpResponse(
                data,
                status=206,
                content_type='video/mp4'
            )
            response['Content-Range'] = f'bytes {start_byte}-{end_byte}/{file_size}'
            response['Content-Length'] = str(length)
            response['Accept-Ranges'] = 'bytes'
        else:
            # Full file response
            response = HttpResponse(
                FileWrapper(open(file_path, 'rb')),
                content_type='video/mp4'
            )
            response['Content-Length'] = str(file_size)
        
        response['Content-Disposition'] = f'inline; filename="{smart_str(filename)}"'
        response['Cache-Control'] = 'no-cache'
        
        return response

class LessonVideoInfoView(APIView):
    """Get video information including streaming URL"""
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Check access
        if not self._has_access(request.user, lesson):
            return Response(
                {"error": "You don't have access to this lesson"},
                status=status.HTTP_403_FORBIDDEN
            )

        video_info = {
            'lesson_id': lesson.id,
            'lesson_title': lesson.title,
            'has_video': bool(lesson.video_file or lesson.video_url),
            'video_type': lesson.video_source,
            'duration': lesson.duration,
            'thumbnail_url': request.build_absolute_uri(lesson.thumbnail.url) if lesson.thumbnail else None,
        }

        # Add appropriate video URL based on source type
        if lesson.video_file:
            video_info['video_url'] = request.build_absolute_uri(
                f'/api/lessons/{lesson.id}/stream/'
            )
        elif lesson.video_url:
            video_info['video_url'] = lesson.video_url

        return Response(video_info)

    def _has_access(self, user, lesson):
        """Same access check as above"""
        if not lesson.module.course.is_paid:
            return True
        
        enrollment = Enrollment.objects.filter(
            user=user,
            course=lesson.module.course,
            payment_status__in=['completed', 'free']
        ).first()
        
        return enrollment is not None
    

class MarkCourseCompleteView(APIView):
    """Mark a course as completed for the current user"""
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        try:
            course = get_object_or_404(Course, id=course_id)
            user = request.user
            
            # Get user's enrollment
            enrollment = Enrollment.objects.filter(
                user=user,
                course=course
            ).first()
            
            if not enrollment:
                return Response(
                    {"error": "You are not enrolled in this course."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Mark enrollment as completed
            enrollment.completed = True
            enrollment.completed_at = timezone.now()
            enrollment.save()
            
            # Mark all lessons in the course as completed
            lessons = Lesson.objects.filter(module__course=course)
            for lesson in lessons:
                progress, created = CourseProgress.objects.get_or_create(
                    enrollment=enrollment,
                    lesson=lesson,
                    defaults={
                        'completed': True,
                        'completed_at': timezone.now()
                    }
                )
                if not progress.completed:
                    progress.completed = True
                    progress.completed_at = timezone.now()
                    progress.save()
            
            serializer = EnrollmentSerializer(enrollment, context={'request': request})
            return Response({
                "message": "Course marked as completed successfully",
                "enrollment": serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )