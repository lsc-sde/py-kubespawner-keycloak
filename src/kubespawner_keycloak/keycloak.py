import base64
from kubespawner.spawner import KubeSpawner
from secrets import token_hex
from .objects import (
    KeycloakGroup
)
from .exceptions import (
    InvalidKeycloakGroupPath, 
    InvalidKeycloakResponseCodeException,
    KeycloakGroupNotFoundException,
    NoAssignedValidWorkspaces
)
import requests

class KeycloakRequester:
    def __init__(self, base_url : str, token_url : str, client_id : str, client_secret : str, cacerts : str):
        self.base_url = base_url
        self.token_url = token_url
        self.cacerts = cacerts
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = ""

    def convertToBase64(self, originalValue):
        originalValue_bytes = originalValue.encode("ascii") 
    
        base64_bytes = base64.b64encode(originalValue_bytes) 
        return base64_bytes.decode("ascii")
    
    def get_access_token(self):
        print(f"Requesting {self.token_url} for token")
        credentials_encoded = self.convertToBase64(f"{self.client_id}:{self.client_secret}")
        headers = {"Authorization": f"Basic {credentials_encoded}" } 
        response = requests.post(self.token_url, headers=headers, data = {"grant_type": "client_credentials"}, verify=self.cacerts)
        json = self.process_response(response)   
        self.access_token = json.get("access_token")
        self.access_token_expires_in = json.get("expires_in")
    
    def process_response(self, response):
        if response.status_code == 200:
            return response.json()
        else:
            raise InvalidKeycloakResponseCodeException(response.status_code)

    def query(self, url):
        if self.access_token == "":
            self.get_access_token()

        print(f"Requesting {url}")
        headers = {"Authorization": f"Bearer {self.access_token}" } 
        response = requests.get(f"{self.base_url}{url}", headers=headers, verify=self.cacerts)
        return self.process_response(response)   

class KubespawnerKeycloak:
    def __init__(self, spawner : KubeSpawner, base_url : str, token_url : str, client_id : str, client_secret : str, environments_config : dict = {}, cacerts = "/etc/ssl/certs/ca-certificates.crt", groups_claim = "realm_groups", parent_group_name : str = "jupyter-workspaces"):
        self.requester : KeycloakRequester = KeycloakRequester(base_url, token_url, client_id, client_secret, cacerts=cacerts)
        self.token_url : str = token_url
        self.spawner : KubeSpawner = spawner
        self.user_name : str = spawner.user.name
        self.environments_config = environments_config
        self.parent_group_name : str = parent_group_name
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
    
