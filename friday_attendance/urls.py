from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FridayMeetingSessionViewSet, FridayAttendanceRecordViewSet

router = DefaultRouter()
router.register('sessions', FridayMeetingSessionViewSet, basename='friday-session')
router.register('records', FridayAttendanceRecordViewSet, basename='friday-record')

urlpatterns = [
    path('', include(router.urls)),
]
