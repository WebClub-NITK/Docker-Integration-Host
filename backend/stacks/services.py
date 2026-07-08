import os
import tempfile
import subprocess
import yaml
import logging
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class StackService:
    @staticmethod
    def _get_docker_host_arg(host):
        if host.ip_address in ('127.0.0.1', 'localhost', '::1'):
            return []  # use default local socket
        return ["-H", f"tcp://{host.ip_address}:{host.port}"]

    @staticmethod
    def deploy_stack(stack):
        stack.status = stack.Status.STARTING
        stack.error_message = ""
        stack.save(update_fields=['status', 'error_message'])
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                compose_path = os.path.join(tmpdir, "docker-compose.yml")
                with open(compose_path, "w") as f:
                    f.write(stack.compose_file)
                
                cmd = ["docker"] + StackService._get_docker_host_arg(stack.host) + ["compose", "-p", stack.name, "-f", compose_path, "up", "-d"]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    stack.status = stack.Status.FAILED
                    stack.error_message = result.stderr or result.stdout
                else:
                    stack.status = stack.Status.RUNNING
                    
        except Exception as e:
            logger.error(f"Failed to deploy stack {stack.name}: {e}")
            stack.status = stack.Status.FAILED
            stack.error_message = str(e)
            
        stack.save(update_fields=['status', 'error_message'])

    @staticmethod
    def teardown_stack(stack):
        stack.status = stack.Status.REMOVING
        stack.save(update_fields=['status'])
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                compose_path = os.path.join(tmpdir, "docker-compose.yml")
                with open(compose_path, "w") as f:
                    f.write(stack.compose_file)
                
                cmd = ["docker"] + StackService._get_docker_host_arg(stack.host) + ["compose", "-p", stack.name, "-f", compose_path, "down"]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    stack.status = stack.Status.FAILED
                    stack.error_message = result.stderr or result.stdout
                else:
                    stack.status = stack.Status.STOPPED
                    
        except Exception as e:
            logger.error(f"Failed to teardown stack {stack.name}: {e}")
            stack.status = stack.Status.FAILED
            stack.error_message = str(e)
            
        stack.save(update_fields=['status', 'error_message'])

    @staticmethod
    def parse_compose(compose_file):
        try:
            data = yaml.safe_load(compose_file)
            services = data.get('services', {})
            nodes = []
            edges = []
            
            for s_name, s_config in services.items():
                nodes.append({
                    "id": s_name,
                    "type": "service",
                    "data": {
                        "label": s_name,
                        "image": s_config.get('image', 'build'),
                        "ports": s_config.get('ports', []),
                    }
                })
                
                depends_on = s_config.get('depends_on', [])
                if isinstance(depends_on, dict):
                    depends_on = list(depends_on.keys())
                    
                for dep in depends_on:
                    edges.append({
                        "id": f"e-{s_name}-{dep}",
                        "source": s_name,
                        "target": dep,
                        "label": "depends on"
                    })
                    
                networks = s_config.get('networks', [])
                if isinstance(networks, dict):
                    networks = list(networks.keys())
                for net in networks:
                    net_id = f"net-{net}"
                    if not any(n['id'] == net_id for n in nodes):
                        nodes.append({
                            "id": net_id,
                            "type": "network",
                            "data": {"label": net}
                        })
                    edges.append({
                        "id": f"e-{s_name}-{net_id}",
                        "source": s_name,
                        "target": net_id,
                        "label": "connects"
                    })
                    
                volumes = s_config.get('volumes', [])
                for vol in volumes:
                    vol_name = vol.split(':')[0] if isinstance(vol, str) else vol.get('source')
                    if vol_name and not vol_name.startswith('.') and not vol_name.startswith('/'):
                        vol_id = f"vol-{vol_name}"
                        if not any(n['id'] == vol_id for n in nodes):
                            nodes.append({
                                "id": vol_id,
                                "type": "volume",
                                "data": {"label": vol_name}
                            })
                        edges.append({
                            "id": f"e-{s_name}-{vol_id}",
                            "source": s_name,
                            "target": vol_id,
                            "label": "mounts"
                        })
                        
            return {"nodes": nodes, "edges": edges}
        except Exception as e:
            logger.error(f"Failed to parse compose file: {e}")
            raise ValidationError(f"Invalid Compose file: {str(e)}")
