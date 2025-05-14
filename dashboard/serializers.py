# dashboard/serializers.py
from rest_framework import serializers
from service_requests.models import ServiceRequest
from accounts.models import UserProfile
from django.db.models import Count
from collections import OrderedDict

class DashboardStatsSerializer(serializers.Serializer):
    """
    Serializer for dashboard statistics
    """
    total_requests = serializers.IntegerField()
    new_requests = serializers.IntegerField()
    in_progress_requests = serializers.IntegerField()
    completed_requests = serializers.IntegerField()
    high_priority_requests = serializers.IntegerField()
    urgent_requests = serializers.IntegerField()
    
    # Staff-only stats
    unassigned_requests = serializers.IntegerField(required=False)
    total_customers = serializers.IntegerField(required=False)
    
    def to_representation(self, instance):
        """
        Filter out staff-only fields for customer users
        """
        result = super().to_representation(instance)
        request = self.context.get('request')
        
        if request and not request.user.is_staff_member:
            # Remove staff-only fields for customers
            staff_only_fields = ['unassigned_requests', 'total_customers']
            for field in staff_only_fields:
                if field in result:
                    result.pop(field)
        
        return result

class CategoryBreakdownSerializer(serializers.Serializer):
    """
    Serializer for request distribution by category
    """
    category_name = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()

class StatusBreakdownSerializer(serializers.Serializer):
    """
    Serializer for request distribution by status
    """
    status = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()

class PriorityBreakdownSerializer(serializers.Serializer):
    """
    Serializer for request distribution by priority
    """
    priority = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()

class AgentPerformanceSerializer(serializers.Serializer):
    """
    Serializer for agent performance metrics
    """
    agent_name = serializers.CharField()
    assigned_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()
    resolution_rate = serializers.FloatField()
    avg_completion_time = serializers.DurationField(allow_null=True)