import socket

class NetworkUtils:
    def getIp():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = socket.gethostname()
        finally:
            s.close()
        return IP
