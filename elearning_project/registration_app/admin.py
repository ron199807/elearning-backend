# registration_app/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# class CustomUserAdmin(UserAdmin):
#     list_display = ('username', 'email', 'is_staff', 'is_instructor', 'is_student_property')
#     list_filter = ('is_staff', 'is_instructor', 'is_student_filter')
#     fieldsets = (
#         (None, {'fields': ('username', 'password')}),
#         ('Personal Info', {'fields': ('email',)}),
#         ('Permissions', {'fields': ('is_staff', 'is_instructor', 'role')}),  # Include `role` if it exists
#     )
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_instructor', 'role'),
#         }),
#     )
#     search_fields = ('username', 'email')
#     ordering = ('username',)

#     def is_student_property(self, obj):
#         return obj.role == "student"  # Assuming you have a `role` field
#     is_student_property.short_description = 'Is Student'
#     is_student_property.boolean = True

#     def is_student_filter(self, obj):
#         return obj.role == "student"  # Assuming you have a `role` field
#     is_student_filter.short_description = 'Is Student'

# Register the CustomUser model
admin.site.register(CustomUser)