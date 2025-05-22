# service_requests/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import (
    ServiceCategory,
    ServiceRequest,
    RequestAttachment,
    RequestComment,
    RequestStatusHistory
)
from .serializers import (
    ServiceCategorySerializer,
    ServiceRequestListSerializer,
    ServiceRequestDetailSerializer,
    ServiceRequestCreateSerializer,
    RequestAttachmentSerializer,
    RequestCommentSerializer,
    RequestStatusHistorySerializer
)

class IsCustomerOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow customers to see their own requests
    and staff to see all requests.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Staff can see all requests
        if request.user.is_staff_member:
            return True
        
        # Customers can only see their own requests
        return obj.customer == request.user

class ServiceCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing service categories
    """
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

class ServiceRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for service requests
    """
    permission_classes = [IsCustomerOrStaff]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'request_id', 'service_address']
    ordering_fields = ['created_at', 'updated_at', 'status', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff_member:
            # Staff can see all requests
            return ServiceRequest.objects.all()
        else:
            # Customers can only see their own requests
            return ServiceRequest.objects.filter(customer=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ServiceRequestCreateSerializer
        elif self.action == 'list':
            return ServiceRequestListSerializer
        return ServiceRequestDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get comments for a specific request"""
        service_request = self.get_object()
        user = request.user
        
        # Get comments based on user role
        if user.is_staff_member:
            comments = service_request.comments.all()
        else:
            comments = service_request.comments.filter(is_internal=False)
        
        serializer = RequestCommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def attachments(self, request, pk=None):
        """Get attachments for a specific request"""
        service_request = self.get_object()
        attachments = service_request.attachments.all()
        serializer = RequestAttachmentSerializer(attachments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        service_request = self.get_object()
        is_internal = request.data.get('is_internal', False)
        
        # Only staff can create internal comments
        if is_internal and not request.user.is_staff_member:
            is_internal = False
        
        comment = RequestComment.objects.create(
            service_request=service_request,
            author=request.user,
            text=request.data.get('text', ''),
            is_internal=is_internal
        )
        
        serializer = RequestCommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def upload_attachment(self, request, pk=None):
        service_request = self.get_object()
        
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        attachment = RequestAttachment.objects.create(
            service_request=service_request,
            file=file,
            file_name=file.name,
            uploaded_by=request.user
        )
        
        serializer = RequestAttachmentSerializer(attachment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        # Only staff can change status
        if not request.user.is_staff_member:
            return Response(
                {'error': 'Only staff can change request status'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        service_request = self.get_object()
        new_status = request.data.get('status')
        comment = request.data.get('comment', '')
        
        # Validate status
        valid_statuses = [choice[0] for choice in ServiceRequest.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Track status change
        previous_status = service_request.status
        
        # Update status
        service_request.status = new_status
        
        # If status is completed, set completed_at
        if new_status == ServiceRequest.COMPLETED and previous_status != ServiceRequest.COMPLETED:
            service_request.completed_at = timezone.now()
        
        service_request.save()
        
        # Create status history entry
        status_history = RequestStatusHistory.objects.create(
            service_request=service_request,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=request.user,
            comment=comment
        )
        
        # Return updated request
        serializer = self.get_serializer(service_request)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        # Only staff can assign requests
        if not request.user.is_staff_member:
            return Response(
                {'error': 'Only staff can assign requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        service_request = self.get_object()
        staff_id = request.data.get('staff_id')
        
        from accounts.models import UserProfile
        
        # If staff_id is None, unassign
        if staff_id is None:
            service_request.assigned_to = None
            service_request.save()
            return Response({'success': 'Request unassigned'})
        
        # Find the staff member
        try:
            staff_member = UserProfile.objects.get(
                id=staff_id,
                role__in=[UserProfile.SUPPORT_AGENT, UserProfile.MANAGER, UserProfile.ADMIN]
            )
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'Staff member not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Assign the request
        service_request.assigned_to = staff_member
        service_request.save()
        
        serializer = self.get_serializer(service_request)
        return Response(serializer.data)