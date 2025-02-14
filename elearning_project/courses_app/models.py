from django.db import models
from django.conf import settings
from django.utils.text import slugify

from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='course_images/', null=True, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False) 
    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses")
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="enrolled_courses", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    duration = models.PositiveIntegerField(help_text="Duration in hours", null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def clean(self):
        if self.price < 0:
            raise ValidationError({"price": "Price cannot be negative."})

    class Meta:
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['created_at']),
        ]