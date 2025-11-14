from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import (
    Category, Course, CourseModule, 
    Lesson, CourseMaterial, Enrollment
)

# Custom admin site settings
admin.site.site_header = "Course Platform Administration"
admin.site.site_title = "Course Platform Admin Portal"
admin.site.index_title = "Welcome to Course Platform Admin"

# Resources for import/export
class CourseResource(resources.ModelResource):
    class Meta:
        model = Course
        fields = ('id', 'title', 'instructor__username', 'price', 'is_paid', 'duration', 'category__name')

class EnrollmentResource(resources.ModelResource):
    class Meta:
        model = Enrollment
        fields = ('id', 'user__username', 'course__title', 'enrolled_at', 'payment_status', 'completed')

# Inline Admins
class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1
    fields = ('title', 'order', 'video_url', 'content')
    ordering = ('order',)

class CourseMaterialInline(admin.StackedInline):
    model = CourseMaterial
    extra = 1
    fields = ('title', 'file', 'description')
    readonly_fields = ('uploaded_at',)
    ordering = ('uploaded_at',)

class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    fields = ('course', 'enrolled_at', 'payment_status', 'completed')
    readonly_fields = ('enrolled_at',)
    can_delete = False

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    inlines = [EnrollmentInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'enrollment_count')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    
    def enrollment_count(self, obj):
        return obj.enrollment_set.count()
    enrollment_count.short_description = 'Enrollments'

# First unregister the User model if it's already registered
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# Then register with our custom admin
admin.site.register(User, CustomUserAdmin)

# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'course_count')
    search_fields = ('name', 'description')
   
    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = 'Courses'

# Course Admin
@admin.register(Course)
class CourseAdmin(ImportExportModelAdmin):
    resource_class = CourseResource
    list_display = ('title', 'instructor', 'price', 'is_paid', 'student_count', 'created_at')
    list_filter = ('is_paid', 'category', 'created_at')
    search_fields = ('title', 'description', 'instructor__username')
    filter_horizontal = ('students',)
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('instructor',)
    actions = ['make_free', 'make_paid']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'instructor')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Pricing', {
            'fields': ('price', 'is_paid')
        }),
        ('Metadata', {
            'fields': ('category', 'duration', 'students')
        }),
    )
    
    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = 'Students'
    
    def make_free(self, request, queryset):
        updated = queryset.update(price=0, is_paid=False)
        self.message_user(request, f"{updated} courses were marked as free.")
    make_free.short_description = "Mark selected courses as free"
    
    def make_paid(self, request, queryset):
        updated = queryset.update(is_paid=True)
        self.message_user(request, f"{updated} courses were marked as paid.")
    make_paid.short_description = "Mark selected courses as paid"

# Course Module Admin
@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'lesson_count')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    ordering = ('course', 'order')
    inlines = [LessonInline]
    
    fieldsets = (
        (None, {
            'fields': ('course', 'title', 'order', 'description')
        }),
    )
    
    def lesson_count(self, obj):
        return obj.lessons.count()
    lesson_count.short_description = 'Lessons'

# Lesson Admin
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'course', 'order', 'material_count')
    list_filter = ('module__course',)
    search_fields = ('title', 'content', 'module__title')
    ordering = ('module', 'order')
    inlines = [CourseMaterialInline]
    raw_id_fields = ('module',)
    
    fieldsets = (
        (None, {
            'fields': ('module', 'title', 'order')
        }),
        ('Content', {
            'fields': ('video_url', 'content')
        }),
    )
    
    def course(self, obj):
        return obj.module.course
    course.admin_order_field = 'module__course'
    
    def material_count(self, obj):
        return obj.materials.count()
    material_count.short_description = 'Materials'

# Course Material Admin
@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'course', 'file_type', 'uploaded_at')
    list_filter = ('lesson__module__course',)
    search_fields = ('title', 'lesson__title')
    date_hierarchy = 'uploaded_at'
    raw_id_fields = ('lesson',)
    
    fieldsets = (
        (None, {
            'fields': ('lesson', 'title', 'file', 'description')
        }),
    )
    
    def course(self, obj):
        return obj.lesson.module.course
    course.admin_order_field = 'lesson__module__course'
    
    def file_type(self, obj):
        if obj.file:
            return obj.file.name.split('.')[-1].upper()
        return "N/A"
    file_type.short_description = 'Type'

# Enrollment Admin
@admin.register(Enrollment)
class EnrollmentAdmin(ImportExportModelAdmin):
    resource_class = EnrollmentResource
    list_display = ('user', 'course', 'enrolled_at', 'payment_status', 'completed', 'days_since_enrollment')
    list_filter = ('payment_status', 'completed', 'course')
    search_fields = ('user__username', 'course__title', 'payment_reference')
    date_hierarchy = 'enrolled_at'
    raw_id_fields = ('user', 'course')
    actions = ['mark_as_completed', 'mark_as_pending', 'mark_as_paid']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'course')
        }),
        ('Status', {
            'fields': ('payment_status', 'payment_reference', 'completed')
        }),
    )
    
    def days_since_enrollment(self, obj):
        from django.utils.timezone import now
        return (now() - obj.enrolled_at).days
    days_since_enrollment.short_description = 'Days Enrolled'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(payment_status='completed', completed=True)
        self.message_user(request, f"{updated} enrollments were marked as completed.")
    mark_as_completed.short_description = "Mark selected as completed"
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(payment_status='pending')
        self.message_user(request, f"{updated} enrollments were marked as pending.")
    mark_as_pending.short_description = "Mark selected as pending"
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(payment_status='completed')
        self.message_user(request, f"{updated} enrollments were marked as paid.")
    mark_as_paid.short_description = "Mark selected as paid"