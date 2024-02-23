from datetime import datetime, timedelta
from exceptions import KeycloakGroupConversionException

class WorkspaceVolumeStatus:
    def __init__(self, name : str, namespace: str, exists : bool):
        self.name = name
        self.exists = exists
        self.namespace = namespace

class KeycloakGroup:
    def __init__(self, group_as_map):
        self.id : int = group_as_map.get("id")
        self.path : str = group_as_map.get("path")
        self.display_name = self.path.split("/")[-1]
        self.workspace_name = self.display_name.lower().replace(" ", "-")

        attributes = group_as_map.get("attributes", {})
        self.environment_name : str = attributes.get("workspace.xlscsde.nhs.uk/environment", [ "jupyter_default" ])[0]
        self.start_date : str = attributes.get("workspace.xlscsde.nhs.uk/startDate", [ "1900-01-01" ])[0]
        self.end_date : str = attributes.get("workspace.xlscsde.nhs.uk/endDate", [ "1900-01-01" ])[0]
        self.description : str = attributes.get("workspace.xlscsde.nhs.uk/description", [ "No description provided" ])[0] 
        
        if not self.id:
            raise KeycloakGroupConversionException(group_as_map, "id not present")
        
        if not self.path:
            raise KeycloakGroupConversionException(group_as_map, "path not present")
        
        if not self.display_name:
            raise KeycloakGroupConversionException(group_as_map, "display_name not present")
        
        if not self.workspace_name:
            raise KeycloakGroupConversionException(group_as_map, "workspace_name not present")
        
    def days_until_expiry(self):
        ws_end_date = datetime.strptime(self.end_date, "%Y-%m-%d")
        ws_days_left: timedelta = ws_end_date - datetime.today()
        return ws_days_left

    def to_workspace_dict(self, kubespawner_override : dict):
        ws = dict()
        ws["display_name"] = self.display_name
        print(kubespawner_override)
        ws["kubespawner_override"] = dict.copy(kubespawner_override)
        ws["kubespawner_override"]["extra_labels"] = {"workspace": self.workspace_name}
        ws["slug"] = self.workspace_name
        ws["start_date"] = self.start_date
        ws["end_date"] = self.end_date
        ws["ws_days_left"] = self.days_until_expiry()
        return ws

