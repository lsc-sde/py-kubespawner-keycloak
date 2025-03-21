"""
Keycloak integration module for KubeSpawner.

This module provides classes for interacting with Keycloak authentication services
and mapping Keycloak groups to Kubernetes workspace configurations for JupyterHub.
It allows retrieving user group memberships and translating them into workspace
access permissions.
"""

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
    """
    Client for making authenticated requests to the Keycloak REST API.
    
    This class handles authentication with Keycloak using client credentials
    and provides methods for making authenticated API requests.
    
    Attributes:
        base_url (str): Base URL of the Keycloak API
        token_url (str): URL for obtaining OAuth access tokens
        cacerts (str): Path to CA certificates file for SSL verification
        client_id (str): OAuth client ID
        client_secret (str): OAuth client secret
        access_token (str): Current OAuth access token
        access_token_expires_in (int): Token expiration time in seconds
    """
    
    def __init__(self, base_url : str, token_url : str, client_id : str, client_secret : str, cacerts : str):
        """
        Initialize a new KeycloakRequester.
        
        Args:
            base_url (str): Base URL of the Keycloak API
            token_url (str): URL for obtaining OAuth access tokens
            client_id (str): OAuth client ID
            client_secret (str): OAuth client secret
            cacerts (str): Path to CA certificates file for SSL verification
        """
        self.base_url = base_url
        self.token_url = token_url
        self.cacerts = cacerts
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = ""

    def convertToBase64(self, originalValue):
        """
        Convert a string to its base64 encoded representation.
        
        Args:
            originalValue (str): The string to encode
            
        Returns:
            str: Base64 encoded string
        """
        originalValue_bytes = originalValue.encode("ascii") 
    
        base64_bytes = base64.b64encode(originalValue_bytes) 
        return base64_bytes.decode("ascii")
    
    def get_access_token(self):
        """
        Obtain an OAuth access token from Keycloak using client credentials.
        
        Makes a request to the token endpoint using Basic authentication with
        client credentials, then stores the returned access token for later use.
        
        Raises:
            InvalidKeycloakResponseCodeException: If the token request fails
        """
        print(f"Requesting {self.token_url} for token")
        credentials_encoded = self.convertToBase64(f"{self.client_id}:{self.client_secret}")
        headers = {"Authorization": f"Basic {credentials_encoded}" } 
        response = requests.post(self.token_url, headers=headers, data = {"grant_type": "client_credentials"}, verify=self.cacerts)
        json = self.process_response(response)   
        self.access_token = json.get("access_token")
        self.access_token_expires_in = json.get("expires_in")
    
    def process_response(self, response):
        """
        Process an HTTP response from Keycloak.
        
        Checks the response status code and returns the JSON content if successful.
        
        Args:
            response (requests.Response): HTTP response object
            
        Returns:
            dict: JSON response content
            
        Raises:
            InvalidKeycloakResponseCodeException: If the response status code is not 200
        """
        if response.status_code == 200:
            return response.json()
        else:
            raise InvalidKeycloakResponseCodeException(response.status_code)

    def query(self, url):
        """
        Make an authenticated GET request to the Keycloak API.
        
        Obtains an access token if needed, then makes a GET request to the specified
        endpoint using Bearer token authentication.
        
        Args:
            url (str): API endpoint path to query (will be appended to base_url)
            
        Returns:
            dict: JSON response from the API
            
        Raises:
            InvalidKeycloakResponseCodeException: If the request fails
        """
        if self.access_token == "":
            self.get_access_token()

        print(f"Requesting {url}")
        headers = {"Authorization": f"Bearer {self.access_token}" } 
        response = requests.get(f"{self.base_url}{url}", headers=headers, verify=self.cacerts)
        return self.process_response(response)   


class KubespawnerKeycloak:
    """
    Integration between KubeSpawner and Keycloak for workspace management.
    
    This class retrieves user group memberships from Keycloak and maps them to
    workspace configurations for JupyterHub. It allows determining which workspaces
    a user has access to based on their Keycloak group memberships.
    
    Attributes:
        requester (KeycloakRequester): Client for making Keycloak API requests
        token_url (str): URL for obtaining OAuth access tokens
        spawner (KubeSpawner): KubeSpawner instance
        user_name (str): Username of the current user
        environments_config (dict): Configuration overrides for different environments
        parent_group_name (str): Name of the parent Keycloak group containing workspace groups
        groups (list): List of Keycloak groups the user belongs to
    """
    
    def __init__(self, spawner : KubeSpawner, base_url : str, token_url : str, client_id : str, client_secret : str, environments_config : dict = {}, cacerts = "/etc/ssl/certs/ca-certificates.crt", groups_claim = "realm_groups", parent_group_name : str = "jupyter-workspaces"):
        """
        Initialize a new KubespawnerKeycloak instance.
        
        Args:
            spawner (KubeSpawner): KubeSpawner instance
            base_url (str): Base URL of the Keycloak API
            token_url (str): URL for obtaining OAuth access tokens
            client_id (str): OAuth client ID
            client_secret (str): OAuth client secret
            environments_config (dict, optional): Configuration overrides for different environments. Defaults to {}.
            cacerts (str, optional): Path to CA certificates file. Defaults to "/etc/ssl/certs/ca-certificates.crt".
            groups_claim (str, optional): Name of the claim containing user groups. Defaults to "realm_groups".
            parent_group_name (str, optional): Name of the parent Keycloak group. Defaults to "jupyter-workspaces".
        """
        self.requester : KeycloakRequester = KeycloakRequester(base_url, token_url, client_id, client_secret, cacerts=cacerts)
        self.token_url : str = token_url
        self.spawner : KubeSpawner = spawner
        self.user_name : str = spawner.user.name
        self.environments_config = environments_config
        self.parent_group_name : str = parent_group_name
        userdata = spawner.oauth_user
        self.groups = userdata[groups_claim]

    def get_groups(self):
        """
        Retrieve all groups from Keycloak with their hierarchy.
        
        Returns:
            list: List of all Keycloak groups with their hierarchy
        """
        return self.requester.query(f"/groups?populateHierarchy=true")
    
    def get_group(self, group_id):
        """
        Retrieve a specific Keycloak group by its ID.
        
        Args:
            group_id (str): ID of the group to retrieve
            
        Returns:
            KeycloakGroup: The requested group
        """
        return KeycloakGroup(self.requester.query(f"/groups/{group_id}"))
    
    def get_group_by_name(self, name):
        """
        Retrieve a Keycloak group by its name.
        
        Args:
            name (str): Name of the group to retrieve
            
        Returns:
            dict: The requested group
            
        Raises:
            KeycloakGroupNotFoundException: If no group with the specified name is found
        """
        results = self.requester.query(f"/groups?populateHierarchy=true")
        filtered_results = [g for g in results if g['name'] == name]
        if len(filtered_results) > 0:
            return filtered_results[0]
        else:
            raise KeycloakGroupNotFoundException(name)
       
    def get_group_children(self, group_id):
        """
        Retrieve all child groups of a specific Keycloak group.
        
        Args:
            group_id (str): ID of the parent group
            
        Returns:
            dict: Dictionary mapping group paths (lowercase) to KeycloakGroup objects
        """
        array = self.requester.query(f"/groups/{group_id}/children")
        groups = {}
        for group in array:
            group_definition = KeycloakGroup(group)
            groups[group_definition.path.casefold()] = group_definition

        return groups

    def get_permitted_workspaces(self):
        """
        Determine which workspaces the user has access to based on their Keycloak group memberships.
        
        Retrieves workspace configuration from Keycloak groups and applies environment-specific
        configuration overrides. Caches the results in the spawner's oauth_user dictionary.
        
        Returns:
            list: List of workspace dictionaries the user has access to
            
        Raises:
            NoAssignedValidWorkspaces: If the user has no valid workspace assignments
        """
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

