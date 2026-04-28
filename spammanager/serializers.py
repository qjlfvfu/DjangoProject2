from rest_framework import serializers
from .models import Mailing, Client


class MailingSerializer(serializers.ModelSerializer):
    recipients = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), many=True, required=False
    )

    class Meta:
        model = Mailing
        fields = [
            "id",
            "start_time",
            "end_time",
            "message",
            "recipients",
            "is_active",
            "status",
        ]
        read_only_fields = ["status"]
