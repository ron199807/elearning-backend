# registration_app/admin.py

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from rest_framework.authtoken.models import Token

# Get your custom user model
User = get_user_model()

class CustomUserAdmin(UserAdmin):
    # Customize the admin form if needed
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    filter_horizontal = ()
    list_filter = ('is_staff', 'is_active')

# Register the custom user model with the custom admin interface
admin.site.register(User, CustomUserAdmin)
# Register the Token model
admin.site.register(Token)

# registration_app/admin.py

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from rest_framework.authtoken.models import Token

# Get your custom user model
User = get_user_model()

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    filter_horizontal = ()
    list_filter = ('is_staff', 'is_active')

# Register the custom user model with the custom admin interface
# admin.site.register(User, CustomUserAdmin)

# Register the Token model to manage tokens in the admin
# admin.site.register(Token)












