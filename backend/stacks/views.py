import logging
import threading
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from hosts.models import Host
from images.permissions import IsAdminOrHostOwner
from .models import Stack
from .serializers import StackSerializer, StackCreateSerializer
from .services import StackService

logger = logging.getLogger(__name__)

class StackListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrHostOwner]

    def get_host(self):
        return get_object_or_404(Host, pk=self.kwargs["host_id"])

    def get(self, request, host_id):
        host = self.get_host()
        stacks = Stack.objects.filter(host=host)
        serializer = StackSerializer(stacks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, host_id):
        host = self.get_host()
        serializer = StackCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        stack = Stack.objects.create(
            name=data['name'],
            host=host,
            compose_file=data['compose_file'],
            created_by=request.user,
            status=Stack.Status.CREATED
        )
        
        # Fire background worker to deploy
        def deploy():
            StackService.deploy_stack(stack)
            
        threading.Thread(target=deploy, daemon=True).start()
        
        resp_serializer = StackSerializer(stack)
        return Response(resp_serializer.data, status=status.HTTP_201_CREATED)

class StackDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrHostOwner]

    def get_host(self):
        return get_object_or_404(Host, pk=self.kwargs["host_id"])

    def get(self, request, host_id, stack_id):
        host = self.get_host()
        stack = get_object_or_404(Stack, pk=stack_id, host=host)
        serializer = StackSerializer(stack)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, host_id, stack_id):
        host = self.get_host()
        stack = get_object_or_404(Stack, pk=stack_id, host=host)
        
        def teardown():
            StackService.teardown_stack(stack)
            if stack.status == Stack.Status.STOPPED:
                stack.delete()
                
        threading.Thread(target=teardown, daemon=True).start()
        
        return Response({"detail": "Teardown initiated"}, status=status.HTTP_202_ACCEPTED)

class StackGraphView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrHostOwner]

    def get_host(self):
        return get_object_or_404(Host, pk=self.kwargs["host_id"])

    def get(self, request, host_id, stack_id):
        host = self.get_host()
        stack = get_object_or_404(Stack, pk=stack_id, host=host)
        try:
            graph = StackService.parse_compose(stack.compose_file)
            return Response(graph, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
