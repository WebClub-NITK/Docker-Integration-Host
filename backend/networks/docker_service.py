import logging
import docker
from django.conf import settings
from requests.exceptions import ConnectionError
from hosts.models import Host
from .models import Network

logger = logging.getLogger(__name__)

def _is_local_hostname(hostname: str) -> bool:
    value = (hostname or "").strip().lower()
    return value in {"localhost", "127.0.0.1", "::1"}

def get_client(host: Host) -> docker.DockerClient:
    """
    SDK Connection Factory
    Dynamically initializes a docker.DockerClient based on the Host model's connection parameters.
    """
    if _is_local_hostname(host.ip_address):
        try:
            return docker.from_env(timeout=10)
        except docker.errors.DockerException:
            pass

    base_url = f"tcp://{host.ip_address}:{host.port}"
    
    return docker.DockerClient(base_url=base_url, timeout=10)


def create_network_in_platform(
    host: Host, 
    user, 
    name: str, 
    driver: str = "bridge", 
    subnet: str = None, 
    gateway: str = None, 
    internal: bool = False, 
    attachable: bool = True, 
    labels: dict = None
) -> Network:
    """
    Creates a network on the remote Docker engine AND synchronizes its
    metadata into the Django platform database for persistence tracking.
    """
    try:
        client = get_client(host)
    except Exception as e:
        logger.error(f"Failed to resolve connection factory client parameters for host {host.alias}: {str(e)}")
        raise RuntimeError(f"Engine connection string configurations invalid.")

    ipam_config = None
    if subnet or gateway:
        if not (subnet and gateway):
            raise ValueError("Both subnet and gateway parameters must be provided together for custom static IPAM.")
        
        ipam_pool = docker.types.IPAMPool(subnet=subnet, gateway=gateway)
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])

    try:
        sdk_network = client.networks.create(
            name=name,
            driver=driver,
            internal=internal,
            attachable=attachable,
            labels=labels or {},
            ipam=ipam_config
        )
    except ConnectionError:
        logger.error(f"Host machine engine target unreachable at {host.ip_address}:{host.port}")
        raise RuntimeError("Target Docker daemon engine is currently offline or unreachable.")
    except docker.errors.APIError as e:
        logger.warning(f"Docker API rejection encountered during execution: {e.explanation}")
        raise RuntimeError(f"Docker Daemon Rejection: {e.explanation}")

    try:
        platform_network = Network.objects.create(
            host=host,
            created_by=user,
            docker_network_id=sdk_network.id, 
            name=name,
            driver=driver,
            subnet=subnet,
            gateway=gateway,
            internal=internal,
            attachable=attachable,
            labels=labels or {}
        )
        logger.info(f"User {user.username} successfully registered network '{name}' (ID: {sdk_network.id[:12]}) on host '{host.alias}'.")
        return platform_network
        
    except Exception as db_err:
        logger.critical(f"Critical DB sync desynchronization: deleting orphaned engine network resource. Error: {str(db_err)}")
        try:
            sdk_network.remove()
        except Exception:
            pass
        raise db_err