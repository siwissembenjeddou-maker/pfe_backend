from django.urls import path
from .views import ConversationListView, MessageListView, SendMessageView

urlpatterns = [
    path('',                       SendMessageView.as_view(),      name='send-message'),
    path('conversations',          ConversationListView.as_view(), name='conversation-list'),
    path('conversations/',         ConversationListView.as_view(), name='conversation-list-slash'),
    path('<int:conversation_id>',  MessageListView.as_view(),      name='message-list'),
    path('<int:conversation_id>/', MessageListView.as_view(),      name='message-list-slash'),
]