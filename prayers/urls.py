from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrayerDefinitionViewSet, PrayerLogViewSet

router = DefaultRouter()
router.register('definitions', PrayerDefinitionViewSet, basename='prayer-definition')
router.register('logs', PrayerLogViewSet, basename='prayer-log')

urlpatterns = [
    path('', include(router.urls)),
]
