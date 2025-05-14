from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404

from .models import UserProfile
from .serializers import UserProfileSerializer, CustomerProfileSerializer, StaffProfileSerializer

class IsOwnerOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow owners of an account to view/edit it
    or staff members with appropriate permissions
    """
    def has_object_permission(self, request, view, obj):
        # Staff members can access all accounts
        if request.user.is_staff_member:
            # Managers and admins can do anything
            if request.user.role in [UserProfile.MANAGER, UserProfile.ADMIN]:
                return True
                
            # Support agents can only view
            if request.method in permissions.SAFE_METHODS:
                return True
                
            return False
        
        # Regular users can only see/modify their own accounts
        return obj == request.user

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user profiles
    """
    queryset = UserProfile.objects.all()
    permission_classes = [IsOwnerOrStaff]
    
    def get_serializer_class(self):
        user = self.request.user
        
        # Staff creating/updating a customer
        if user.is_staff_member and self.request.data.get('role') == UserProfile.CUSTOMER:
            return CustomerProfileSerializer
            
        # Staff creating/updating staff
        elif user.is_staff_member and user.role in [UserProfile.MANAGER, UserProfile.ADMIN]:
            return StaffProfileSerializer
            
        # Default
        return UserProfileSerializer
        
    def get_queryset(self):
        user = self.request.user
        
        # Staff can see all profiles based on role
        if user.is_staff_member:
            if user.role in [UserProfile.MANAGER, UserProfile.ADMIN]:
                return UserProfile.objects.all()
            else:
                # Support agents can only see customers
                return UserProfile.objects.filter(role=UserProfile.CUSTOMER)
                
        # Regular users can only see their own profile
        return UserProfile.objects.filter(id=user.id)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        return Response({'success': 'Logged out successfully'})
    
    @action(detail=False, methods=['get'])
    def current_user(self, request):
        """
        Return the currently authenticated user
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Not authenticated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """
        Register a new customer account
        """
        serializer = CustomerProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def staff_users(self, request):
        """
        Get list of staff users (for admins and managers only)
        """
        user = request.user
        if not user.is_staff_member or user.role not in [UserProfile.MANAGER, UserProfile.ADMIN]:
            return Response(
                {'error': 'You do not have permission to view staff users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        staff_users = UserProfile.objects.filter(
            role__in=[UserProfile.SUPPORT_AGENT, UserProfile.MANAGER, UserProfile.ADMIN]
        )
        serializer = StaffProfileSerializer(staff_users, many=True)
        return Response(serializer.data)