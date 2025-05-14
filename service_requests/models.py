# service_requests/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import UserProfile
import uuid

class ServiceCategory(models.Model):
    """
    Categories for different types of service requests
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Service Category')
        verbose_name_plural = _('Service Categories')
    
    def __str__(self):
        return self.name

class ServiceRequest(models.Model):
    """
    Model to track customer service requests
    """
    # Status choices
    NEW = 'new'
    ASSIGNED = 'assigned'
    IN_PROGRESS = 'in_progress'
    ON_HOLD = 'on_hold'
    COMPLETED = 'completed'
    CLOSED = 'closed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (NEW, _('New')),
        (ASSIGNED, _('Assigned')),
        (IN_PROGRESS, _('In Progress')),
        (ON_HOLD, _('On Hold')),
        (COMPLETED, _('Completed')),
        (CLOSED, _('Closed')),
        (CANCELLED, _('Cancelled')),
    ]
    
    # Priority choices
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'
    
    PRIORITY_CHOICES = [
        (LOW, _('Low')),
        (MEDIUM, _('Medium')),
        (HIGH, _('High')),
        (URGENT, _('Urgent')),
    ]
    
    # Request fields
    request_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    customer = models.ForeignKey(
        UserProfile, 
        on_delete=models.CASCADE, 
        related_name='service_requests'
    )
    category = models.ForeignKey(
        ServiceCategory, 
        on_delete=models.PROTECT,
        related_name='requests'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=NEW
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=MEDIUM
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_to = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    service_address = models.TextField(blank=True, null=True)
    gas_meter_id = models.CharField(max_length=30, blank=True, null=True)
    
    class Meta:
        verbose_name = _('Service Request')
        verbose_name_plural = _('Service Requests')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Request {self.request_id} - {self.customer.username}"

class RequestAttachment(models.Model):
    """
    Attachments for service requests (images, documents, etc.)
    """
    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='request_attachments/')
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='uploaded_attachments'
    )
    
    def __str__(self):
        return f"Attachment for {self.service_request.request_id}"

class RequestComment(models.Model):
    """
    Comments on service requests from customers or staff
    """
    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='request_comments'
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_internal = models.BooleanField(default=False, help_text="If true, only visible to staff")
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.service_request.request_id}"

class RequestStatusHistory(models.Model):
    """
    Track status changes for service requests
    """
    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    previous_status = models.CharField(max_length=20, choices=ServiceRequest.STATUS_CHOICES)
    new_status = models.CharField(max_length=20, choices=ServiceRequest.STATUS_CHOICES)
    changed_by = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='status_changes'
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = _('Request Status History')
        verbose_name_plural = _('Request Status Histories')
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"Status change for {self.service_request.request_id}: {self.previous_status} → {self.new_status}"