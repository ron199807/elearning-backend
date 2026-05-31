# admin.py
from django.contrib import admin
from .models import Course, Category, CourseModule, Lesson, CourseMaterial, Enrollment, CourseProgress, Certificate, LessonVideo, LessonContentBlock

# Register LessonVideo inline for Lesson admin
class LessonVideoInline(admin.TabularInline):
    model = LessonVideo
    extra = 1
    fields = ['title', 'video_url', 'video_file', 'order', 'position', 'duration', 'is_preview', 'thumbnail']
    ordering = ['order']

class LessonContentBlockInline(admin.TabularInline):
    model = LessonContentBlock
    extra = 1
    fields = ['block_type', 'content', 'video', 'order', 'custom_css_class']
    ordering = ['order']

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'module', 'order', 'duration', 'is_published', 'is_preview']
    list_filter = ['is_published', 'is_preview', 'module__course']
    search_fields = ['title', 'content']
    list_editable = ['order', 'is_published']
    
    # Remove any reference to 'video_url' or 'video_file' here
    fieldsets = (
        ('Basic Information', {
            'fields': ('module', 'title', 'order', 'content', 'duration', 'is_published', 'is_preview', 'thumbnail')
        }),
        ('Additional Info', {
            'fields': (),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [LessonVideoInline, LessonContentBlockInline]
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Remove any video_url field if it exists in the form
        if 'video_url' in form.base_fields:
            del form.base_fields['video_url']
        if 'video_file' in form.base_fields:
            del form.base_fields['video_file']
        return form

@admin.register(LessonVideo)
class LessonVideoAdmin(admin.ModelAdmin):
    list_display = ['id', 'lesson', 'title', 'order', 'position', 'duration', 'is_preview']
    list_filter = ['position', 'is_preview', 'lesson__module__course']
    search_fields = ['title', 'lesson__title']
    list_editable = ['order', 'position']

@admin.register(LessonContentBlock)
class LessonContentBlockAdmin(admin.ModelAdmin):
    list_display = ['id', 'lesson', 'block_type', 'order']
    list_filter = ['block_type', 'lesson__module__course']
    list_editable = ['order']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'instructor', 'price', 'is_paid', 'status', 'is_published', 'created_at']
    list_filter = ['status', 'is_paid', 'is_published', 'level', 'language']
    search_fields = ['title', 'subtitle', 'description', 'instructor__username']
    list_editable = ['status', 'is_published']
    readonly_fields = ['slug', 'created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'subtitle', 'slug', 'description', 'category', 'instructor', 'image')
        }),
        ('Pricing', {
            'fields': ('price', 'is_paid', 'has_discount', 'discount_price', 'discount_expiry', 'currency')
        }),
        ('Course Details', {
            'fields': ('duration', 'language', 'level', 'status', 'is_published')
        }),
        ('Lists', {
            'fields': ('learning_objectives', 'prerequisites', 'target_audience')
        }),
        ('Messages', {
            'fields': ('welcome_message', 'completion_message'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_public', 'allow_enrollment', 'certificate_available', 'featured', 'max_students'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']
    search_fields = ['name', 'description']

@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'course', 'order', 'is_published']
    list_filter = ['course', 'is_published']
    search_fields = ['title', 'course__title']
    list_editable = ['order', 'is_published']

@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'lesson', 'uploaded_at', 'file']
    list_filter = ['lesson__module__course']
    search_fields = ['title', 'description']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'course', 'enrolled_at', 'completed', 'payment_status']
    list_filter = ['completed', 'payment_status', 'course']
    search_fields = ['user__username', 'course__title']
    readonly_fields = ['enrolled_at', 'completed_at']

@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    list_display = ['id', 'enrollment', 'lesson', 'completed', 'completed_at', 'time_spent']
    list_filter = ['completed', 'enrollment__course']
    search_fields = ['enrollment__user__username', 'lesson__title']

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['id', 'certificate_id', 'student_name', 'course_title', 'issued_at', 'is_verified']
    list_filter = ['is_verified', 'issued_at']
    search_fields = ['certificate_id', 'student_name', 'student_email', 'course_title']
    readonly_fields = ['certificate_id', 'verification_token', 'issued_at']