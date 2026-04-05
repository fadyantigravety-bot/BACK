from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MassAttendanceRecordViewSet

router = DefaultRouter()
router.register('records', MassAttendanceRecordViewSet, basename='mass-record')

urlpatterns = [
    path('', include(router.urls)),
]
