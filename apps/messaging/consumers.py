import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data    = json.loads(text_data)
        content = data.get('content', '')
        user    = self.scope['user']
        msg     = await self.save_message(user, content)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type':       'chat_message',
                'id':         msg.id,
                'sender_id':  user.id,
                'sender_name':user.name,
                'content':    content,
                'created_at': str(msg.created_at),
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, user, content):
        from .models import Message, Conversation
        conv = Conversation.objects.get(pk=self.conversation_id)
        return Message.objects.create(conversation=conv, sender=user, content=content)