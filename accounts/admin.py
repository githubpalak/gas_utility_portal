# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import UserProfile

class CustomUserAdmin(UserAdmin):
    """
    Custom admin for UserProfile
    """
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'address')}),
        (_('Role'), {'fields': ('role',)}),
        (_('Customer info'), {'fields': ('customer_id', 'gas_meter_id', 'service_address')}),
        (_('Staff info'), {'fields': ('department', 'employee_id')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'customer_id', 'gas_meter_id')
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj is None:
            # When creating a new user, add role selection
            return fieldsets
        # For existing users, show relevant fields based on role
        if obj.role == UserProfile.CUSTOMER:
            # Hide staff-specific fields for customers
            return [fs for fs in fieldsets if fs[0] != _('Staff info')]
        else:
            # Hide customer-specific fields for staff
            return [fs for fs in fieldsets if fs[0] != _('Customer info')]

admin.site.register(UserProfile, CustomUserAdmin)