# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class UserProfile(AbstractUser):
    """
    Extended User model for both customers and staff
    """
    CUSTOMER = 'customer'
    SUPPORT_AGENT = 'agent'
    MANAGER = 'manager'
    ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (CUSTOMER, _('Customer')),
        (SUPPORT_AGENT, _('Support Agent')),
        (MANAGER, _('Manager')),
        (ADMIN, _('Admin')),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=CUSTOMER,
    )
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    customer_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # Customer-specific fields
    gas_meter_id = models.CharField(max_length=30, blank=True, null=True)
    service_address = models.TextField(blank=True, null=True)
    
    # Staff-specific fields
    department = models.CharField(max_length=100, blank=True, null=True)
    employee_id = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_customer(self):
        return self.role == self.CUSTOMER
    
    @property
    def is_staff_member(self):
        return self.role in [self.SUPPORT_AGENT, self.MANAGER, self.ADMIN]