# service_requests/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Main router
router = DefaultRouter()
router.register(r'categories', views.ServiceCategoryViewSet)
router.register(r'requests', views.ServiceRequestViewSet, basename='servicerequest')

urlpatterns = [
    path('', include(router.urls)),
]