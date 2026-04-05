from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FollowUpRecordViewSet

router = DefaultRouter()
router.register('records', FollowUpRecordViewSet, basename='followup-record')

urlpatterns = [
    path('', include(router.urls)),
]
