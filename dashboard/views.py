# dashboard/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from collections import OrderedDict

from accounts.models import UserProfile
from service_requests.models import ServiceRequest, ServiceCategory
from .serializers import (
    DashboardStatsSerializer,
    CategoryBreakdownSerializer,
    StatusBreakdownSerializer,
    PriorityBreakdownSerializer,
    AgentPerformanceSerializer
)

class DashboardViewSet(viewsets.ViewSet):
    """
    API endpoint for dashboard statistics and metrics
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get overall dashboard statistics
        """
        user = request.user
        
        # Base queryset based on user role
        if user.is_customer:
            requests_qs = ServiceRequest.objects.filter(customer=user)
        else:
            requests_qs = ServiceRequest.objects.all()
        
        # Calculate basic stats
        total_requests = requests_qs.count()
        new_requests = requests_qs.filter(status=ServiceRequest.NEW).count()
        in_progress_requests = requests_qs.filter(
            status__in=[ServiceRequest.ASSIGNED, ServiceRequest.IN_PROGRESS]
        ).count()
        completed_requests = requests_qs.filter(status=ServiceRequest.COMPLETED).count()
        high_priority_requests = requests_qs.filter(priority=ServiceRequest.HIGH).count()
        urgent_requests = requests_qs.filter(priority=ServiceRequest.URGENT).count()
        
        stats_data = {
            'total_requests': total_requests,
            'new_requests': new_requests,
            'in_progress_requests': in_progress_requests,
            'completed_requests': completed_requests,
            'high_priority_requests': high_priority_requests,
            'urgent_requests': urgent_requests,
        }
        
        # Add staff-only stats
        if user.is_staff_member:
            stats_data.update({
                'unassigned_requests': requests_qs.filter(assigned_to__isnull=True).count(),
                'total_customers': UserProfile.objects.filter(role=UserProfile.CUSTOMER).count(),
            })
        
        serializer = DashboardStatsSerializer(stats_data, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def category_breakdown(self, request):
        """
        Get breakdown of requests by category
        """
        user = request.user
        
        # Base queryset based on user role
        if user.is_customer:
            requests_qs = ServiceRequest.objects.filter(customer=user)
        else:
            requests_qs = ServiceRequest.objects.all()
        
        # Get category breakdown
        category_data = requests_qs.values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        total = requests_qs.count()
        breakdown_data = []
        
        for item in category_data:
            percentage = (item['count'] / total * 100) if total > 0 else 0
            breakdown_data.append({
                'category_name': item['category__name'],
                'count': item['count'],
                'percentage': round(percentage, 2)
            })
        
        serializer = CategoryBreakdownSerializer(breakdown_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def status_breakdown(self, request):
        """
        Get breakdown of requests by status
        """
        user = request.user
        
        # Base queryset based on user role
        if user.is_customer:
            requests_qs = ServiceRequest.objects.filter(customer=user)
        else:
            requests_qs = ServiceRequest.objects.all()
        
        # Get status breakdown
        status_data = requests_qs.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        total = requests_qs.count()
        breakdown_data = []
        
        for item in status_data:
            percentage = (item['count'] / total * 100) if total > 0 else 0
            status_display = dict(ServiceRequest.STATUS_CHOICES).get(item['status'], item['status'])
            breakdown_data.append({
                'status': status_display,
                'count': item['count'],
                'percentage': round(percentage, 2)
            })
        
        serializer = StatusBreakdownSerializer(breakdown_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def priority_breakdown(self, request):
        """
        Get breakdown of requests by priority
        """
        user = request.user
        
        # Base queryset based on user role
        if user.is_customer:
            requests_qs = ServiceRequest.objects.filter(customer=user)
        else:
            requests_qs = ServiceRequest.objects.all()
        
        # Get priority breakdown
        priority_data = requests_qs.values('priority').annotate(
            count=Count('id')
        ).order_by('-count')
        
        total = requests_qs.count()
        breakdown_data = []
        
        for item in priority_data:
            percentage = (item['count'] / total * 100) if total > 0 else 0
            priority_display = dict(ServiceRequest.PRIORITY_CHOICES).get(item['priority'], item['priority'])
            breakdown_data.append({
                'priority': priority_display,
                'count': item['count'],
                'percentage': round(percentage, 2)
            })
        
        serializer = PriorityBreakdownSerializer(breakdown_data, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def agent_performance(self, request):
        """
        Get agent performance metrics (staff only)
        """
        user = request.user
        
        if not user.is_staff_member or user.role not in [UserProfile.MANAGER, UserProfile.ADMIN]:
            return Response(
                {'error': 'You do not have permission to view agent performance'},
                status=403
            )
        
        # Get all support agents
        agents = UserProfile.objects.filter(role=UserProfile.SUPPORT_AGENT)
        performance_data = []
        
        for agent in agents:
            assigned_requests = ServiceRequest.objects.filter(assigned_to=agent)
            completed_requests = assigned_requests.filter(status=ServiceRequest.COMPLETED)
            
            assigned_count = assigned_requests.count()
            completed_count = completed_requests.count()
            resolution_rate = (completed_count / assigned_count * 100) if assigned_count > 0 else 0
            
            # Calculate average completion time
            completed_with_times = completed_requests.filter(
                completed_at__isnull=False
            )
            
            if completed_with_times.exists():
                avg_time = completed_with_times.aggregate(
                    avg_time=Avg('completed_at') - Avg('created_at')
                )['avg_time']
            else:
                avg_time = None
            
            performance_data.append({
                'agent_name': f"{agent.first_name} {agent.last_name}",
                'assigned_count': assigned_count,
                'completed_count': completed_count,
                'resolution_rate': round(resolution_rate, 2),
                'avg_completion_time': avg_time
            })
        
        serializer = AgentPerformanceSerializer(performance_data, many=True)
        return Response(serializer.data)