import socket
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

def is_port_available(port: int, host: str = "localhost") -> bool:
    """Check if a port is available on the given host"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0  # 0 means the port is in use
    except Exception as e:
        logger.warning(f"Error checking port {port}: {e}")
        return False

def find_available_port(preferred_port: int, port_range: Optional[List[int]] = None, host: str = "localhost") -> int:
    """Find an available port, starting with the preferred port"""
    if is_port_available(preferred_port, host):
        return preferred_port
    
    # If preferred port is not available, try a range of ports
    if port_range is None:
        port_range = list(range(preferred_port + 1, preferred_port + 100))
    
    for port in port_range:
        if is_port_available(port, host):
            logger.info(f"Port {preferred_port} was in use, using port {port} instead")
            return port
    
    raise RuntimeError(f"No available ports found in range starting from {preferred_port}")

def get_service_port(service_name: str, default_port: int, host: str = "localhost") -> int:
    """Get an available port for a service, with environment variable override"""
    import os
    
    # Try to get port from environment variable
    env_port = os.getenv(f"{service_name.upper()}_SERVICE_PORT")
    if env_port:
        try:
            preferred_port = int(env_port)
        except ValueError:
            logger.warning(f"Invalid port in environment variable for {service_name}: {env_port}")
            preferred_port = default_port
    else:
        preferred_port = default_port
    
    return find_available_port(preferred_port, host=host) 