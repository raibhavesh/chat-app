import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from ChatApp.models import *
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = f"room_{self.scope['url_route']['kwargs']['room_name']}"
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json
        encrypted_message, iv = self.encrypt_message(message['message'])  # Return IV for decryption

        event = {
            'type': 'send_message',
            'message': {**message, 'message': encrypted_message, 'iv': iv},
        }

        await self.channel_layer.group_send(self.room_name, event)

    async def send_message(self, event):
        encrypted_data = event['message']['message']
        iv = bytes.fromhex(event['message']['iv'])  # Get IV from the event

        decrypted_message = self.decrypt_message(encrypted_data, iv)  # Decrypt using the IV

        # Save the message to the database asynchronously
        await self.create_message(data={'sender': event['message']['sender'], 'message': decrypted_message, 'room_name': event['message']['room_name']})

        response_data = {
            'sender': event['message']['sender'],
            'message': decrypted_message
        }
        await self.send(text_data=json.dumps({'message': response_data}))

    @database_sync_to_async
    def create_message(self, data):
        get_room_by_name = Room.objects.get(room_name=data['room_name'])

        if not Message.objects.filter(message=data['message']).exists():
            new_message = Message(room=get_room_by_name, sender=data['sender'], message=data['message'])
            new_message.save()

    def encrypt_message(self, message):
        password = b"supersecretpassword"  # Ensure this is kept secret and secure
        salt = os.urandom(16)  # Generate a random salt

        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
        key = kdf.derive(password)

        iv = os.urandom(16)  # Generate a random IV
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        padded_message = message + (16 - len(message) % 16) * " "  # Pad the message to be a multiple of 16
        encrypted_message = encryptor.update(padded_message.encode()) + encryptor.finalize()

        return encrypted_message.hex(), iv.hex()  # Return encrypted message and IV as hex

    def decrypt_message(self, encrypted_message, iv):
        password = b"supersecretpassword"  # Ensure this is kept secret and secure
        salt = os.urandom(16)  # Normally you would have a fixed salt per user or session

        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
        key = kdf.derive(password)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())  # Use the same IV
        decryptor = cipher.decryptor()

        decrypted_message = decryptor.update(bytes.fromhex(encrypted_message)) + decryptor.finalize()
        return decrypted_message.decode().strip()  # Remove padding and decode

