import logging
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings
from .models import CustomUser
from courses_app.models import Course
from rest_framework.permissions import BasePermission

logger = logging.getLogger(__name__)

class IsInstructor(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and 
            request.user.role == 'instructor'
        )

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and 
            request.user.role == 'student'
        )

class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and 
            request.user.role == 'admin'
        )

# Optional: Create a flexible permission for enrollment
class CanEnrollInCourse(BasePermission):
    """
    Allow any authenticated user to enroll in courses
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

@receiver(post_migrate)
def setup_instructor_group(sender, **kwargs):
    """
    Creates the 'Instructors' group, assigns permissions, and adds an example user to the group.
    Runs after migrations to ensure the database is ready.
    """
    if sender.name == "courses_app":  # Ensure it runs only for the relevant app
        # Get ContentType for Course
        content_type = ContentType.objects.get_for_model(Course)

        # Create Instructor Group if it doesn't exist
        instructor_group, created = Group.objects.get_or_create(name="Instructors")

        # Get or create necessary permissions (Example: 'add_course', 'change_course', 'delete_course')
        permissions = Permission.objects.filter(
            content_type=content_type,
            codename__in=["add_course", "change_course", "delete_course"]
        )
        instructor_group.permissions.set(permissions)  # Assign permissions to group

        if created:
            logger.info("Instructor Group created.")
        else:
            logger.info("Instructor Group already exists.")
        logger.info(f"Assigned Permissions: {list(permissions.values_list('codename', flat=True))}")

        # Assign a user to the instructor group (if user exists)
        try:
            user = CustomUser.objects.get(username=settings.INSTRUCTOR_USERNAME)
            user.groups.add(instructor_group)
            logger.info(f"User {user.username} added to 'Instructors' group.")
        except CustomUser.DoesNotExist:
            logger.warning(f"User '{settings.INSTRUCTOR_USERNAME}' does not exist yet.")