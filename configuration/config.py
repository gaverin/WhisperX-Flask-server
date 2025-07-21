import os
import json
from configuration.compute_power import ComputePower
from configuration.transcription_mode import TranscriptionMode
from configuration.server_settings import ServerSettings
from configuration.transcription_settings import TranscriptionSettings

class Config():
    """
        Validates the configuration parameters and sets them in the right place.
        Data validation is done on setting so only valid config files are saved.
    """

    def __init__(self, config_file_path: str):
        #Check if file exists
        if not os.path.exists(config_file_path):
            raise FileNotFoundError(f"Configuration file not found at {config_file_path}")
        #Save valid path
        self.config_file_path = config_file_path
        #Parse file
        with open(self.config_file_path, "r") as f:
            config_dict = json.load(f)
            self._config_dict = config_dict

            server_settings_dict = config_dict["server_settings"]
            transcription_settings_dict = config_dict["transcription_settings"]

            self._server_settings = ServerSettings(server_settings_dict["address"], server_settings_dict["port"])
            self._transcription_settings = TranscriptionSettings(transcription_settings_dict["compute_power"], 
                    transcription_settings_dict["transcription_mode"], transcription_settings_dict["num_jobs"])

    @staticmethod
    def validate(config_dict):
        # Check if 'server_settings' exists and is a dictionary with valid keys
        if not isinstance(config_dict.get('server_settings'), dict):
            return False
        server_settings = config_dict['server_settings']
        if not ServerSettings.validate(server_settings):
            return False

        # Check if 'transcription_settings' exists and is a dictionary with valid keys
        if not isinstance(config_dict.get('transcription_settings'), dict):
            return False
        transcription_settings = config_dict['transcription_settings']
        if not TranscriptionSettings.validate(transcription_settings):
            return False

        return True
    
    def get_config(self):
        return self._config_dict

    def get_config_options(self):
        return self._transcription_settings.get_options()
    
    def get_server_settings(self):
        return self._server_settings

    def get_transcription_settings(self):
        return self._transcription_settings


