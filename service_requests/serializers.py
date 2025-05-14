# service_requests/serializers.py
from rest_framework import serializers
from .models import ServiceCategory, ServiceRequest, RequestAttachment, RequestComment, RequestStatusHistory
from accounts.serializers import UserProfileSerializer

class ServiceCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for service categories
    """
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'description', 'slug', 'is_active']

class RequestAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for service request attachments
    """
    uploaded_by = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = RequestAttachment
        fields = ['id', 'file', 'file_name', 'uploaded_at', 'uploaded_by']
        read_only_fields = ['uploaded_at', 'uploaded_by']

class RequestCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for comments on service requests
    """
    author = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = RequestComment
        fields = ['id', 'text', 'created_at', 'author', 'is_internal']
        read_only_fields = ['created_at', 'author']

class RequestStatusHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for tracking status changes
    """
    changed_by = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = RequestStatusHistory
        fields = ['id', 'previous_status', 'new_status', 'changed_at', 'changed_by', 'comment']
        read_only_fields = ['changed_at', 'changed_by']

class ServiceRequestListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing service requests
    """
    customer_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'request_id', 'title', 'status', 'priority',
            'created_at', 'updated_at', 'customer_name',
            'category_name', 'assigned_to_name'
        ]
    
    def get_customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}"
    
    def get_category_name(self, obj):
        return obj.category.name
    
    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}"
        return None

class ServiceRequestDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for service request details
    """
    customer = UserProfileSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    assigned_to = UserProfileSerializer(read_only=True)
    attachments = RequestAttachmentSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    status_history = RequestStatusHistorySerializer(many=True, read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.all(),
        write_only=True,
        source='category'
    )
    
    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'request_id', 'customer', 'category', 'category_id',
            'title', 'description', 'status', 'priority',
            'created_at', 'updated_at', 'assigned_to',
            'completed_at', 'service_address', 'gas_meter_id',
            'attachments', 'comments', 'status_history'
        ]
        read_only_fields = [
            'request_id', 'customer', 'created_at', 
            'updated_at', 'assigned_to', 'completed_at'
        ]
    
    def get_comments(self, obj):
        # Filter comments based on user role
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return []
        
        # Get all comments for staff, only public comments for customers
        if request.user.is_staff_member:
            comments = obj.comments.all()
        else:
            comments = obj.comments.filter(is_internal=False)
        
        return RequestCommentSerializer(comments, many=True).data

class ServiceRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new service requests
    """
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.all(),
        source='category'
    )
    
    class Meta:
        model = ServiceRequest
        fields = [
            'category_id', 'title', 'description', 
            'priority', 'service_address', 'gas_meter_id'
        ]
    
    def create(self, validated_data):
        # Set the customer to the current user
        request = self.context.get('request')
        validated_data['customer'] = request.user
        
        # Create the service request
        return super().create(validated_data)