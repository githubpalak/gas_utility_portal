# service_requests/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views

# Main router
router = DefaultRouter()
router.register(r'categories', views.ServiceCategoryViewSet)
router.register(r'requests', views.ServiceRequestViewSet, basename='servicerequest')

# Nested routers for attachments and comments
service_requests_router = routers.NestedSimpleRouter(router, r'requests', lookup='service_request')
service_requests_router.register(r'attachments', views.RequestAttachmentViewSet, basename='request-attachments')
service_requests_router.register(r'comments', views.RequestCommentViewSet, basename='request-comments')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(service_requests_router.urls)),
]