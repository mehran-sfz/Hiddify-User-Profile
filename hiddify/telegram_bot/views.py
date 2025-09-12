import logging

from accounts.models import Profile
from django.db import transaction
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from telegram_bot.models import Telegram_account

logger = logging.getLogger(__name__)

class TelegramWebhookSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()
    telegram_id = serializers.CharField()
    first_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    username = serializers.CharField(required=False, allow_null=True, allow_blank=True)

class TelegramWebhookView(APIView):

    def post(self, request, *args, **kwargs):
        try:
            # Extract message
            data = request.data.get('message', {}).get('from', {})
            if not data:
                return Response({'status': 'fail', 'error': 'Invalid payload.'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate input
            serializer = TelegramWebhookSerializer(data=data)
            if not serializer.is_valid():
                return Response({'status': 'fail', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            uuid = validated_data['uuid']
            telegram_id = validated_data['telegram_id']
            first_name = validated_data.get('first_name', '')
            last_name = validated_data.get('last_name', '')
            username = validated_data.get('username', '')

            # Check for profile
            try:
                profile = Profile.objects.get(uuid=uuid)
            except Profile.DoesNotExist:
                return Response({'status': 'fail', 'error': 'Profile with the given UUID does not exist.'}, status=status.HTTP_404_NOT_FOUND)

            logger.error(f"Profile: {profile}")

            # Create Telegram account
            Telegram_account.objects.create(
                user=profile.user,
                first_name=first_name,
                last_name=last_name,
                telegram_user_id=telegram_id,
                username=username
            )

            return Response({'status': 'success', 'message': 'Telegram account created successfully.'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({'status': 'fail', 'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
