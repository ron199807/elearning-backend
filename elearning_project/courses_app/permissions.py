from rest_framework import permissions

class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow instructors to create/edit courses.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to instructors
        return hasattr(request.user, 'is_instructor') and request.user.is_instructor

class IsCourseInstructor(permissions.BasePermission):
    """
    Custom permission to only allow course instructor to modify course content.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is the instructor of the course
        if hasattr(obj, 'instructor'):
            return obj.instructor == request.user
        elif hasattr(obj, 'course'):
            return obj.course.instructor == request.user
        elif hasattr(obj, 'module'):
            return obj.module.course.instructor == request.user
        return False

class IsEnrolledStudent(permissions.BasePermission):
    """
    Custom permission to only allow enrolled students to access course content.
    """
    def has_object_permission(self, request, view, obj):
        from .models import Enrollment
        
        # Get the course from different object types
        if hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'module'):
            course = obj.module.course
        elif hasattr(obj, 'lesson'):
            course = obj.lesson.module.course
        else:
            return False
        
        # Check if user is enrolled in the course
        return Enrollment.objects.filter(
            user=request.user,
            course=course
        ).exists()