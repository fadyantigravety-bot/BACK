from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConfessionRecordViewSet, DailyConfessionListView, MarkConfessionAttendanceView

router = DefaultRouter()
router.register('records', ConfessionRecordViewSet, basename='confession-record')

urlpatterns = [
    path('daily-attendance/', DailyConfessionListView.as_view(), name='daily-attendance'),
    path('mark-attendance/', MarkConfessionAttendanceView.as_view(), name='mark-attendance'),
    path('', include(router.urls)),
]
