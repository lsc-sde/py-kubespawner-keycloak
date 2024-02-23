from kubespawner.spawner import KubeSpawner
from datetime import datetime, timedelta
import requests

class InvalidKeycloakGroupPath(Exception):
    def __init__(self, group_name, parent_group_name):
        self.group_name = group_name
        self.parent_group_name = parent_group_name
        self.message = f"Group Path: {group_name} does not begin with /{parent_group_name}/"
        super().__init__(self.message)

class InvalidKeycloakResponseCodeException(Exception):
    def __init__(self, received_code, expected_code = 200):
        self.received_code = received_code
        self.expected_code = expected_code
        self.message = f"Expected Keycloak response of {expected_code} but received {received_code}"
        super().__init__(self.message)

class KeycloakGroupConversionException(Exception):
    def __init__(self, group_definition, inner_message):
        self.group_definition = group_definition
        self.message = f"Error Converting the group definition: {inner_message}"
        super().__init__(self.message)

class KeycloakGroupNotFoundException(Exception):
    def __init__(self, group_name):
        self.group_name = group_name
        self.message = f"Could not find the group: {group_name}"
        super().__init__(self.message)

class NoAssignedValidWorkspaces(Exception):
    def __init__(self, user):
        self.user = user
        self.message = f"User {user} does not have any valid workspaces assigned"
        super().__init__(self.message)

class KubespawnerKeycloak:
    def __init__(self, spawner, base_url, access_token, environments_config : dict = {}, cacerts = "/etc/ssl/certs/ca-certificates.crt", groups_claim = "realm_groups", parent_group_name : str = "jupyter-workspaces"):
        self.requester : KeycloakRequester = KeycloakRequester(base_url, access_token = access_token, cacerts=cacerts)
        self.spawner : KubeSpawner = spawner
        self.user_name : str = spawner.user.name
        self.environments_config = environments_config
        self.parent_group_name = parent_group_name
        userdata = spawner.oauth_user
        self.groups = userdata[groups_claim]

    def get_groups(self):
        return self.requester.query(f"/groups?populateHierarchy=true")
    
    def get_group(self, group_id):
        return KeycloakGroup(self.requester.query(f"/groups/{group_id}"))
    
    def get_group_by_name(self, name):
        results = self.requester.query(f"/groups?populateHierarchy=true")
        filtered_results = [g for g in results if g['name'] == name]
        if len(filtered_results) > 0:
            return filtered_results[0]
        else:
            raise KeycloakGroupNotFoundException(name)
       
    def get_group_children(self, group_id):
        array = self.requester.query(f"/groups/{group_id}/children")
        groups = {}
        for group in array:
            group_definition = KeycloakGroup(group)
            groups[group_definition.path.casefold()] = group_definition

        return groups

    def get_permitted_workspaces(self):
        permitted_workspaces = []
        if "permitted_workspaces" in self.spawner.oauth_user:
            return self.spawner.oauth_user
        
        parent_group = self.get_group_by_name(self.parent_group_name)
        
        available_groups = self.get_group_children(parent_group["id"])

        # iterating through the group_name
        for group_name in self.groups:
            if not group_name.startswith(f"/{self.parent_group_name}/"):
                e = InvalidKeycloakGroupPath(group_name, self.parent_group_name)
                self.spawner.log.error(e.message)
                continue
            
            group : KeycloakGroup = available_groups[group_name.casefold()]
            print(f"Getting environment config for {group.environment_name}")
            workspace_dict = group.to_workspace_dict(
                kubespawner_override= self.environments_config.get(group.environment_name, {})
            )
            permitted_workspaces.append(workspace_dict)

        if len(permitted_workspaces) == 0:
            raise NoAssignedValidWorkspaces(self.user_name)

        print(f"Permitted Workspaces = {permitted_workspaces}")

        sorted_workspaces = sorted(
            permitted_workspaces, key=lambda x: x.get("slug", "99_Z")
        )

        self.spawner.oauth_user["permitted_workspaces"] = permitted_workspaces
        return permitted_workspaces
    
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

class KeycloakRequester:
    def __init__(self, base_url, access_token, cacerts):
        self.base_url = base_url
        self.access_token = access_token
        self.cacerts = cacerts

    def process_response(self, response):
        if response.status_code == 200:
            return response.json()
        else:
            raise InvalidKeycloakResponseCodeException(response.status_code)

    def query(self, url):
        print(f"Requesting {url}")
        headers = {"Authorization": f"Bearer {self.access_token}" } 
        response = requests.get(f"{self.base_url}{url}", headers=headers, verify=self.cacerts)
        return self.process_response(response)

    