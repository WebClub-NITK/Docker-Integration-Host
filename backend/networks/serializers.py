from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Network

User = get_user_model()

class NetworkSerializer(serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(read_only=True, slug_field='username')
    host = serializers.SlugRelatedField(read_only=True, slug_field='alias')
    labels = serializers.JSONField(required=False, default=dict)

    class Meta:
        model = Network
        fields = [
            'id', 'host', 'docker_network_id', 'name', 'driver', 'subnet', 
            'gateway', 'internal', 'attachable', 'labels', 'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'docker_network_id', 'created_by', 'created_at']

class NetworkCreateSerializer(NetworkSerializer):
    pass