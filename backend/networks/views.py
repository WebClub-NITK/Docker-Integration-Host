import logging
import docker
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound

from .models import Network
from .serializers import NetworkSerializer, NetworkCreateSerializer
from hosts.models import Host
from .docker_service import create_network_in_platform, get_client 
from hosts.permissions import CanAccessHost

logger = logging.getLogger(__name__)

# ==========================================
# 1. NETWORK LIST + CREATE VIEW
# ==========================================
class NetworkListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, CanAccessHost]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return NetworkCreateSerializer
        return NetworkSerializer

    def get_queryset(self):
        return Network.objects.filter(host_id=self.kwargs['host_id'])

    def perform_create(self, serializer):
        host_id = self.kwargs.get('host_id')
        
        try:
            host = Host.objects.get(id=host_id)
        except Host.DoesNotExist:
            raise NotFound({"error": "Target infrastructure host daemon record not found."})

        user_role_mapping = host.user_roles.filter(user=self.request.user).first()
        is_admin = self.request.user.is_superuser or (user_role_mapping and user_role_mapping.role == 'ADMIN')
        is_owner = user_role_mapping and user_role_mapping.role == 'HOST_OWNER'
        
        if not (is_admin or is_owner):
            raise PermissionDenied({"error": "Viewer role cannot modify resources or create networks."})

        v_data = serializer.validated_data
        
        try:
            platform_network = create_network_in_platform(
                host=host,
                user=self.request.user,
                name=v_data['name'],
                driver=v_data.get('driver', 'bridge'),
                subnet=v_data.get('subnet'),
                gateway=v_data.get('gateway'),
                internal=v_data.get('internal', False),
                attachable=v_data.get('attachable', True),
                labels=v_data.get('labels', {})
            )
            serializer.instance = platform_network
            
        except (RuntimeError, ValueError) as sdk_err:
            raise ValidationError({"error": str(sdk_err)})


# ==========================================
# 2. NETWORK DETAIL + RETRIEVE / DESTROY VIEW
# ==========================================
class NetworkDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = NetworkSerializer
    permission_classes = [IsAuthenticated, CanAccessHost]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return Network.objects.filter(host_id=self.kwargs['host_id'])

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        
        try:
            client = get_client(instance.host)
            docker_net = client.networks.get(instance.docker_network_id)
            
            data['options'] = docker_net.attrs.get('Options', {})
            
            containers = {}
            for cid, cinfo in docker_net.attrs.get('Containers', {}).items():
                ipv4 = cinfo.get('IPv4Address', '')
                if '/' in ipv4:
                    ipv4 = ipv4.split('/')[0]
                containers[cid] = {
                    'name': cinfo.get('Name', ''),
                    'Name': cinfo.get('Name', ''),
                    'ipv4_address': ipv4,
                    'IPv4Address': ipv4,
                    'mac_address': cinfo.get('MacAddress', ''),
                    'MacAddress': cinfo.get('MacAddress', '')
                }
            data['containers'] = containers
            
        except Exception as e:
            logger.warning(f"Failed to fetch live details for network {instance.name}: {str(e)}")
            data['options'] = {}
            data['containers'] = {}
            
        return Response(data)

    def perform_destroy(self, instance):
        host = instance.host

        user_role_mapping = host.user_roles.filter(user=self.request.user).first()
        is_admin = self.request.user.is_superuser or (user_role_mapping and user_role_mapping.role == 'ADMIN')
        is_owner = user_role_mapping and user_role_mapping.role == 'HOST_OWNER'
        
        if not (is_admin or is_owner):
            raise PermissionDenied({"error": "Viewer role cannot delete network resources."})

        try:
            client = get_client(host)
            docker_net = client.networks.get(instance.docker_network_id)
            docker_net.remove()
            
            instance.delete()
            logger.info(f"Network '{instance.name}' removed from database and host '{host.alias}'.")

        except docker.errors.APIError as e:
            if "has active endpoints" in str(e) or e.response.status_code == 409:
                raise ValidationError({
                    "error": "Network has active endpoints. Disconnect all containers before deleting."
                })
            raise ValidationError({"error": f"Docker Daemon Exception: {e.explanation}"})
            
        except Exception as conn_err:
            raise ValidationError({"error": "Could not execute teardown sequence. Target daemon node is unreachable."})


# ==========================================
# 3. NETWORK CONTAINER CONNECT / DISCONNECT
# ==========================================
class NetworkConnectContainerView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, CanAccessHost]
    
    def post(self, request, host_id, id):
        try:
            network = Network.objects.get(id=id, host_id=host_id)
        except Network.DoesNotExist:
            raise NotFound({"error": "Network not found."})
            
        host = network.host
        user_role_mapping = host.user_roles.filter(user=request.user).first()
        is_admin = request.user.is_superuser or (user_role_mapping and user_role_mapping.role == 'ADMIN')
        is_owner = user_role_mapping and user_role_mapping.role == 'HOST_OWNER'
        
        if not (is_admin or is_owner):
            raise PermissionDenied({"error": "Viewer role cannot connect containers to networks."})
            
        container_id = request.data.get('container_id')
        if not container_id:
            raise ValidationError({"error": "container_id parameter is required."})
            
        aliases = request.data.get('aliases')
        ipv4_address = request.data.get('ipv4_address')
        
        try:
            client = get_client(host)
            docker_net = client.networks.get(network.docker_network_id)
            
            connect_kwargs = {}
            if aliases:
                connect_kwargs['aliases'] = aliases
            if ipv4_address:
                connect_kwargs['ipv4_address'] = ipv4_address
                
            docker_net.connect(container_id, **connect_kwargs)
            
            # Fetch assigned IP if not passed explicitly
            if not ipv4_address:
                try:
                    container_obj = client.containers.get(container_id)
                    net_settings = container_obj.attrs.get('NetworkSettings', {})
                    networks_settings = net_settings.get('Networks', {})
                    net_config = networks_settings.get(docker_net.name, {}) or networks_settings.get(network.name, {})
                    assigned_ip = net_config.get('IPAddress')
                    if assigned_ip:
                        ipv4_address = assigned_ip
                except Exception:
                    pass
            
            res_data = {
                "message": f"Container {container_id} connected to network {network.name}."
            }
            if ipv4_address:
                res_data["ipv4_address"] = ipv4_address
                
            return Response(res_data, status=status.HTTP_200_OK)
        except docker.errors.APIError as e:
            raise ValidationError({"error": f"Docker Daemon Exception: {e.explanation}"})
        except Exception as conn_err:
            raise ValidationError({"error": "Target daemon node is unreachable."})


class NetworkDisconnectContainerView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, CanAccessHost]
    
    def post(self, request, host_id, id):
        try:
            network = Network.objects.get(id=id, host_id=host_id)
        except Network.DoesNotExist:
            raise NotFound({"error": "Network not found."})
            
        host = network.host
        user_role_mapping = host.user_roles.filter(user=request.user).first()
        is_admin = request.user.is_superuser or (user_role_mapping and user_role_mapping.role == 'ADMIN')
        is_owner = user_role_mapping and user_role_mapping.role == 'HOST_OWNER'
        
        if not (is_admin or is_owner):
            raise PermissionDenied({"error": "Viewer role cannot disconnect containers from networks."})
            
        container_id = request.data.get('container_id')
        if not container_id:
            raise ValidationError({"error": "container_id parameter is required."})
            
        try:
            client = get_client(host)
            docker_net = client.networks.get(network.docker_network_id)
            docker_net.disconnect(container_id, force=request.data.get('force', False))
            
            return Response({
                "message": f"Container {container_id} disconnected from network {network.name}."
            }, status=status.HTTP_200_OK)
        except docker.errors.APIError as e:
            raise ValidationError({"error": f"Docker Daemon Exception: {e.explanation}"})
        except Exception as conn_err:
            raise ValidationError({"error": "Target daemon node is unreachable."})


# ==========================================
# 4. NETWORK PRUNE VIEW
# ==========================================
class NetworkPruneView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, CanAccessHost]
    
    def post(self, request, host_id):
        try:
            host = Host.objects.get(id=host_id)
        except Host.DoesNotExist:
            raise NotFound({"error": "Host not found."})
            
        user_role_mapping = host.user_roles.filter(user=request.user).first()
        is_admin = request.user.is_superuser or (user_role_mapping and user_role_mapping.role == 'ADMIN')
        
        if not is_admin:
            raise PermissionDenied({"error": "Only ADMIN role can prune unused networks."})
            
        try:
            client = get_client(host)
            prune_result = client.networks.prune()
            deleted_names = prune_result.get('NetworksDeleted') or []
            
            if deleted_names:
                Network.objects.filter(host=host, name__in=deleted_names).delete()
                
            return Response({
                "networks_deleted": deleted_names,
                "message": f"{len(deleted_names)} unused networks removed."
            }, status=status.HTTP_200_OK)
        except docker.errors.APIError as e:
            raise ValidationError({"error": f"Docker Daemon Exception: {e.explanation}"})
        except Exception as conn_err:
            raise ValidationError({"error": "Target daemon node is unreachable."})