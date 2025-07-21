import re

class ServerSettings():

    def __init__(self, address, port):
        self._address = address
        self._port = port

    def get_address(self):
        return self._address
    
    def get_port(self):
        return self._port
    
    @staticmethod
    def validate(server_settings):
        if not all(key in server_settings for key in ['address', 'port']):
            return False
        if not isinstance(server_settings['address'], str):
            return False
        pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if not bool(re.match(pattern, server_settings['address'])):
            return False
        if not isinstance(server_settings['port'], int):
            return False
        
        return True
