from kubespawner.spawner import KubeSpawner
from secrets import token_hex
from objects import (
    KeycloakGroup
)
from exceptions import (
    InvalidKeycloakGroupPath, 
    InvalidKeycloakResponseCodeException,
    KeycloakGroupNotFoundException,
    NoAssignedValidWorkspaces
)
import requests

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
    
