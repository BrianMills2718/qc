#!/usr/bin/env python3
"""
Docker Dependency Manager - Fail-Fast Neo4j Container Validation
"""
import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DockerDependencyError(Exception):
    """Raised when Docker dependencies are not met"""
    pass


class DockerManager:
    """Manages Docker container dependencies with fail-fast validation"""
    
    def __init__(self):
        self.docker_available = None
        self.neo4j_container_running = None
    
    def check_docker_available(self) -> bool:
        """Check if Docker is installed and running"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Docker available: {result.stdout.strip()}")
                self.docker_available = True
                return True
            else:
                logger.error("Docker command failed")
                self.docker_available = False
                return False
        except FileNotFoundError:
            logger.error("Docker not installed or not in PATH")
            self.docker_available = False
            return False
        except Exception as e:
            logger.error(f"Docker check failed: {e}")
            self.docker_available = False
            return False
    
    def check_neo4j_container(self, container_name: str = "neo4j") -> Dict[str, Any]:
        """Check Neo4j container status with detailed information"""
        if not self.check_docker_available():
            raise DockerDependencyError("Docker not available - cannot check Neo4j container")
        
        try:
            # Check if container exists and its status
            result = subprocess.run([
                'docker', 'ps', '-a', '--filter', f'name={container_name}', 
                '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise DockerDependencyError(f"Failed to check Neo4j container: {result.stderr}")
            
            output_lines = result.stdout.strip().split('\n')
            if len(output_lines) < 2:  # Only header line present
                raise DockerDependencyError(f"Neo4j container '{container_name}' not found")
            
            container_info = output_lines[1].split('\t')
            status = container_info[1] if len(container_info) > 1 else "unknown"
            ports = container_info[2] if len(container_info) > 2 else "none"
            
            is_running = 'Up' in status
            self.neo4j_container_running = is_running
            
            return {
                'name': container_name,
                'status': status,
                'ports': ports,
                'running': is_running
            }
        
        except Exception as e:
            raise DockerDependencyError(f"Neo4j container check failed: {e}")
    
    def find_running_neo4j_container(self, bolt_port: int = 7687, http_port: int = 7474) -> Optional[Dict[str, Any]]:
        """Find any running Neo4j container by checking for Neo4j image and ports"""
        if not self.check_docker_available():
            raise DockerDependencyError("Docker not available - cannot check Neo4j containers")
        
        try:
            # Look for containers running Neo4j image (use simple format with | separator)
            result = subprocess.run([
                'docker', 'ps', '--format', '{{.Names}}|{{.Status}}|{{.Ports}}|{{.Image}}'
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines:
                    if line.strip():
                        parts = line.split('|')
                        if len(parts) >= 4:
                            name, status, ports, image = parts[0], parts[1], parts[2], parts[3]
                            if 'Up' in status and ('neo4j' in image.lower() or 'neo4j' in name.lower()):
                                logger.info(f"Found Neo4j container: {name} ({image}) - {status}")
                                return {
                                    'name': name.strip(),
                                    'status': status.strip(), 
                                    'ports': ports.strip(),
                                    'image': image.strip(),
                                    'running': True
                                }
            
            # Fallback: look for any container with Neo4j ports exposed
            result = subprocess.run([
                'docker', 'ps', '--format', '{{.Names}}|{{.Status}}|{{.Ports}}|{{.Image}}'
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines:
                    if line.strip():
                        parts = line.split('|')
                        if len(parts) >= 3:
                            name, status, ports = parts[0], parts[1], parts[2]
                            image = parts[3] if len(parts) >= 4 else "unknown"
                            if 'Up' in status and (str(bolt_port) in ports or str(http_port) in ports):
                                logger.info(f"Found container with Neo4j ports: {name} - {ports}")
                                return {
                                    'name': name.strip(),
                                    'status': status.strip(),
                                    'ports': ports.strip(), 
                                    'image': image.strip(),
                                    'running': True
                                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find running Neo4j containers: {e}")
            return None

    def ensure_neo4j_ready(self, container_name: str = "neo4j", 
                          bolt_port: int = 7687, http_port: int = 7474) -> Dict[str, Any]:
        """Ensure Neo4j container is running and ready for connections"""
        
        # First try to find any running Neo4j container
        running_container = self.find_running_neo4j_container(bolt_port, http_port)
        if running_container:
            logger.info(f"Found running Neo4j container: {running_container['name']} - {running_container['status']}")
            return running_container
        
        # Fallback to specific container name check
        try:
            container_info = self.check_neo4j_container(container_name)
            if container_info['running']:
                logger.info(f"Neo4j container ready: {container_info['name']} - {container_info['status']}")
                return container_info
        except DockerDependencyError:
            pass  # Continue to error below
        
        # No running Neo4j container found
        raise DockerDependencyError(
            f"No running Neo4j container found. "
            f"Expected container '{container_name}' or any Neo4j container on ports {bolt_port},{http_port}. "
            f"Start one with: docker run -d --name {container_name} "
            f"-p {bolt_port}:7687 -p {http_port}:7474 "
            f"-e NEO4J_AUTH=neo4j/password neo4j:latest"
        )


# Global instance
docker_manager = DockerManager()


def require_neo4j(container_name: str = "neo4j") -> Dict[str, Any]:
    """Decorator/utility to require Neo4j container before operations"""
    return docker_manager.ensure_neo4j_ready(container_name)


def check_neo4j_dependencies() -> bool:
    """Quick check for Neo4j dependencies - returns True if ready"""
    try:
        docker_manager.ensure_neo4j_ready()
        return True
    except DockerDependencyError as e:
        logger.error(f"Neo4j dependency check failed: {e}")
        return False