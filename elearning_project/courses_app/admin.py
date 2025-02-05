from django.contrib import admin
from .models import Course, Category

# Register the Category model
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    ordering = ('name',)

# Register the Course model
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'price', 'created_at')
    list_filter = ('instructor', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('title',)
    filter_horizontal = ('students',)  # For many-to-many fields

    class CourseAdmin(admin.ModelAdmin):
        filter_horizontal = ('students',)  # Adds a nice widget for selecting students