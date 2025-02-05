from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    is_staff = models.BooleanField(default=False)
    is_instructor = models.BooleanField(default=False)

    @property
    def is_student(self):
        return self.role == "student"