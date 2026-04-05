from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConfessionRecordViewSet

router = DefaultRouter()
router.register('records', ConfessionRecordViewSet, basename='confession-record')

urlpatterns = [
    path('', include(router.urls)),
]
