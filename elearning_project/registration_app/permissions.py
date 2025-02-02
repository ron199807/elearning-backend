from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import CustomUser
from courses_app.models import Course
from rest_framework.permissions import BasePermission

class IsInstructor(BasePermission):
    def has_permission(self, request, view):
         return bool(request.user and request.user.is_authenticated and getattr(request.user, "is_instructor", False))


@receiver(post_migrate)
def setup_instructor_group(sender, **kwargs):
    """
    Creates the 'Instructors' group, assigns permissions, and adds an example user to the group.
    Runs after migrations to ensure database is ready.
    """
    if sender.name == "courses_app":  # Ensure it runs only for the relevant app
        # Get ContentType for Course
        content_type = ContentType.objects.get_for_model(Course)

        # Create Instructor Group if it doesn't exist
        instructor_group, created = Group.objects.get_or_create(name="Instructors")

        # Get or create necessary permissions (Example: 'add_course' and 'change_course')
        permissions = Permission.objects.filter(content_type=content_type)
        instructor_group.permissions.set(permissions)  # Assign permissions to group

        print(f"Instructor Group Setup: {'Created' if created else 'Already Exists'}")
        print(f"Assigned Permissions: {list(permissions.values_list('codename', flat=True))}")

        # Assign a user to the instructor group (if user exists)
        try:
            user = CustomUser.objects.get(username="instructor_user")
            user.groups.add(instructor_group)
            print(f"User {user.username} added to 'Instructors' group.")
        except CustomUser.DoesNotExist:
            print("User 'instructor_user' does not exist yet.")
