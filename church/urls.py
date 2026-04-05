from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceStageViewSet, ServiceGroupViewSet

router = DefaultRouter()
router.register('stages', ServiceStageViewSet, basename='stage')
router.register('groups', ServiceGroupViewSet, basename='group')

urlpatterns = [
    path('', include(router.urls)),
]
