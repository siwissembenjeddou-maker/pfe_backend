from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from apps.users.models import User
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        conv_id = self.kwargs['conversation_id']
        Message.objects.filter(
            conversation_id=conv_id, is_read=False
        ).exclude(sender=self.request.user).update(is_read=True)
        return Message.objects.filter(conversation_id=conv_id)


class SendMessageView(APIView):
    def post(self, request):
        recipient_id = request.data.get('recipient_id')
        content      = request.data.get('content', '').strip()

        if not content:
            return Response({'error': 'content is required'}, status=400)
        try:
            recipient = User.objects.get(pk=recipient_id)
        except User.DoesNotExist:
            return Response({'error': 'Recipient not found'}, status=404)

        conv, _ = Conversation.get_or_create_between(request.user, recipient)
        msg     = Message.objects.create(conversation=conv, sender=request.user, content=content)
        conv.save()
        return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)