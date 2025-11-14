from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError
import json
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('pending', 'Pending Review'),
    ]
    
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('all', 'All Levels'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
        ('zh', 'Chinese'),
    ]

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
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
    
    # New fields for advanced course creation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    learning_objectives = models.JSONField(default=list, blank=True)
    prerequisites = models.JSONField(default=list, blank=True)
    target_audience = models.JSONField(default=list, blank=True)
    welcome_message = models.TextField(blank=True, null=True)
    completion_message = models.TextField(blank=True, null=True)
    certificate_available = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    max_students = models.PositiveIntegerField(default=0)  # 0 means unlimited
    currency = models.CharField(max_length=3, default='USD')
    
    # Discount fields
    has_discount = models.BooleanField(default=False)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_expiry = models.DateTimeField(null=True, blank=True)
    
    # Visibility and access
    is_public = models.BooleanField(default=True)
    allow_enrollment = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Ensure JSON fields are properly formatted
        if isinstance(self.learning_objectives, str):
            try:
                self.learning_objectives = json.loads(self.learning_objectives)
            except json.JSONDecodeError:
                self.learning_objectives = []
        
        if isinstance(self.prerequisites, str):
            try:
                self.prerequisites = json.loads(self.prerequisites)
            except json.JSONDecodeError:
                self.prerequisites = []
        
        if isinstance(self.target_audience, str):
            try:
                self.target_audience = json.loads(self.target_audience)
            except json.JSONDecodeError:
                self.target_audience = []
                
        super().save(*args, **kwargs)

    def clean(self):
        if self.price < 0:
            raise ValidationError({"price": "Price cannot be negative."})
        if self.price is None:
            raise ValidationError({'price': 'Price cannot be empty.'})
        
        # Validate discount fields
        if self.has_discount:
            if not self.discount_price:
                raise ValidationError({"discount_price": "Discount price is required when discount is enabled."})
            if self.discount_price >= self.price:
                raise ValidationError({"discount_price": "Discount price must be less than regular price."})
        
        # Validate max students
        if self.max_students < 0:
            raise ValidationError({"max_students": "Maximum students cannot be negative."})

    @property
    def is_available(self):
        """Check if course is available for enrollment"""
        if not self.allow_enrollment:
            return False
        if self.max_students > 0 and self.students.count() >= self.max_students:
            return False
        if self.status != 'published':
            return False
        return True

    @property
    def current_price(self):
        """Get current price considering discounts"""
        if self.has_discount and self.discount_price and (
            not self.discount_expiry or self.discount_expiry > timezone.now()
        ):
            return self.discount_price
        return self.price

    class Meta:
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['featured']),
            models.Index(fields=['category']),
            models.Index(fields=['level']),
        ]
        ordering = ['-created_at']

class CourseModule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    is_published = models.BooleanField(default=False)


    class Meta:
        ordering = ['order']
        unique_together = ['course', 'order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

class Lesson(models.Model):
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    video_url = models.URLField(blank=True, null=True)
    video_file = models.FileField(upload_to='lesson_videos/',
                                   blank=True,
                                   null=True,
                                   help_text="Upload video file for secure streaming.")
    content = models.TextField(blank=True, null=True)
    duration = models.PositiveIntegerField(help_text="Duration in minutes", default=0)
    is_published = models.BooleanField(default=False)
    is_preview = models.BooleanField(default=False)
    thumbnail = models.ImageField(upload_to='lesson_thumbnails/', null=True, blank=True)
    materials = models.ManyToManyField('CourseMaterial', related_name='lessons', blank=True)

    @property
    def video_source(self):
        """Return the appropriate video source URL or file path"""
        if self.video_file:
            return 'file'
        elif self.video_url:
            return 'url'
        return None


    class Meta:
        ordering = ['order']
        # unique_together = ['module', 'order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"

class CourseMaterial(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='materials_set')
    file = models.FileField(upload_to='course_materials/')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Enrollment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('free', 'Free'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"

class CourseProgress(models.Model):
    """Track student progress through course content"""
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent = models.PositiveIntegerField(default=0)  # in seconds
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['enrollment', 'lesson']

    def __str__(self):
        return f"{self.enrollment.user.username} - {self.lesson.title}"