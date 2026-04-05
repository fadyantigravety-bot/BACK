from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet, MessageViewSet

router = DefaultRouter()
router.register('conversations', ConversationViewSet, basename='conversation')

urlpatterns = [
    path('', include(router.urls)),
    path('conversations/<uuid:conversation_id>/messages/',
         MessageViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='conversation-messages'),
    path('conversations/<uuid:conversation_id>/messages/mark-read/',
         MessageViewSet.as_view({'post': 'mark_read'}),
         name='conversation-mark-read'),
]
