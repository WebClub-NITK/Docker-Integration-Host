from rest_framework import serializers
from .models import Stack

class StackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stack
        fields = ['id', 'name', 'host', 'compose_file', 'status', 'error_message', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['id', 'status', 'error_message', 'created_by', 'created_at', 'updated_at', 'host']

class StackCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    compose_file = serializers.CharField()
