import socket

def find_available_port(start_port=8000, end_port=9000):
    """
    Find an available port in the given range
    
    Args:
        start_port (int): The starting port number
        end_port (int): The ending port number
        
    Returns:
        int or None: An available port number, or None if no port is available
    """
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('localhost', port))
            if result != 0:  # Port is available
                return port
    return None