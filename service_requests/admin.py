from django.contrib import admin
from .models import ServiceCategory, ServiceRequest, RequestAttachment, RequestComment, RequestStatusHistory

class RequestAttachmentInline(admin.TabularInline):
    model = RequestAttachment
    extra = 0
    readonly_fields = ['uploaded_at', 'uploaded_by']

class RequestCommentInline(admin.TabularInline):
    model = RequestComment
    extra = 0
    readonly_fields = ['created_at', 'author']

class RequestStatusHistoryInline(admin.TabularInline):
    model = RequestStatusHistory
    extra = 0
    readonly_fields = ['changed_at', 'changed_by', 'previous_status', 'new_status']
    
@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    list_filter = ['is_active']

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ['request_id', 'title', 'customer', 'category', 'status', 'priority', 'created_at', 'assigned_to']
    list_filter = ['status', 'priority', 'category', 'created_at']
    search_fields = ['title', 'description', 'request_id', 'customer__username', 'customer__email']
    readonly_fields = ['request_id', 'created_at', 'updated_at', 'completed_at']
    inlines = [RequestAttachmentInline, RequestCommentInline, RequestStatusHistoryInline]
    fieldsets = [
        (None, {
            'fields': ['request_id', 'customer', 'category', 'title', 'description']
        }),
        ('Status', {
            'fields': ['status', 'priority', 'assigned_to']
        }),
        ('Dates', {
            'fields': ['created_at', 'updated_at', 'completed_at']
        }),
        ('Customer Information', {
            'fields': ['service_address', 'gas_meter_id']
        }),
    ]
    
    def save_model(self, request, obj, form, change):
        """
        Track status changes when saving from admin
        """
        if change and 'status' in form.changed_data:
            # Get the previous status
            old_obj = ServiceRequest.objects.get(pk=obj.pk)
            previous_status = old_obj.status
            
            # Save the model first
            super().save_model(request, obj, form, change)
            
            # Create status history entry
            RequestStatusHistory.objects.create(
                service_request=obj,
                previous_status=previous_status,
                new_status=obj.status,
                changed_by=request.user,
                comment=f"Status changed from {previous_status} to {obj.status} via admin panel"
            )
        else:
            super().save_model(request, obj, form, change)

@admin.register(RequestAttachment)
class RequestAttachmentAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'service_request', 'uploaded_by', 'uploaded_at']
    search_fields = ['file_name', 'service_request__request_id']
    readonly_fields = ['uploaded_at']

@admin.register(RequestComment)
class RequestCommentAdmin(admin.ModelAdmin):
    list_display = ['service_request', 'author', 'created_at', 'is_internal']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['text', 'service_request__request_id', 'author__username']
    readonly_fields = ['created_at']

@admin.register(RequestStatusHistory)
class RequestStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['service_request', 'previous_status', 'new_status', 'changed_by', 'changed_at']
    list_filter = ['previous_status', 'new_status', 'changed_at']
    search_fields = ['service_request__request_id', 'changed_by__username', 'comment']
    readonly_fields = ['changed_at']