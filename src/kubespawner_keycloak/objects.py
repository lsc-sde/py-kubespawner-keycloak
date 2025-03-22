"""
This module provides the object models for Keycloak integration with Kubespawner.

It defines classes for representing workspace volumes and Keycloak groups with
their respective attributes and methods.
"""

from datetime import datetime, timedelta
from .exceptions import KeycloakGroupConversionException


class WorkspaceVolumeStatus:
    """
    Represents the status of a Kubernetes workspace volume.

    Attributes:
        name (str): The name of the volume.
        namespace (str): The Kubernetes namespace where the volume exists.
        exists (bool): Whether the volume exists in the cluster.
    """

    def __init__(self, name: str, namespace: str, exists: bool):
        self.name = name
        self.exists = exists
        self.namespace = namespace


class KeycloakGroup:
    """
    Represents a Keycloak group with workspace-related attributes.

    This class converts a Keycloak group JSON representation into a Python object
    with workspace-specific properties and helper methods for integration with
    Kubespawner.

    Attributes:
        id (int): The Keycloak group ID.
        path (str): The full path of the group in Keycloak.
        display_name (str): The human-readable name of the workspace.
        workspace_name (str): The Kubernetes-compatible name of the workspace.
        environment_name (str): The environment template to use for this workspace.
        start_date (str): The workspace start date in YYYY-MM-DD format.
        end_date (str): The workspace end date in YYYY-MM-DD format.
        description (str): A description of the workspace purpose.

    Raises:
        KeycloakGroupConversionException: If required attributes are missing.
    """

    def __init__(self, group_as_map):
        self.id: int = group_as_map.get("id")
        self.path: str = group_as_map.get("path")
        self.display_name = self.path.split("/")[-1]
        self.workspace_name = self.display_name.lower().replace(" ", "-")

        attributes = group_as_map.get("attributes", {})
        self.environment_name: str = attributes.get(
            "workspace.xlscsde.nhs.uk/environment", ["jupyter_default"]
        )[0]
        self.start_date: str = attributes.get(
            "workspace.xlscsde.nhs.uk/startDate", ["1900-01-01"]
        )[0]
        self.end_date: str = attributes.get(
            "workspace.xlscsde.nhs.uk/endDate", ["1900-01-01"]
        )[0]
        self.description: str = attributes.get(
            "workspace.xlscsde.nhs.uk/description", ["No description provided"]
        )[0]

        if not self.id:
            raise KeycloakGroupConversionException(group_as_map, "id not present")

        if not self.path:
            raise KeycloakGroupConversionException(group_as_map, "path not present")

        if not self.display_name:
            raise KeycloakGroupConversionException(
                group_as_map, "display_name not present"
            )

        if not self.workspace_name:
            raise KeycloakGroupConversionException(
                group_as_map, "workspace_name not present"
            )

    def days_until_expiry(self):
        """
        Calculate the number of days remaining until the workspace expires.

        Returns:
            timedelta: A timedelta object representing days until expiration.
        """
        ws_end_date = datetime.strptime(self.end_date, "%Y-%m-%d")
        ws_days_left: timedelta = ws_end_date - datetime.today()
        return ws_days_left

    def to_workspace_dict(self, kubespawner_override: dict):
        """
        Convert the KeycloakGroup to a dictionary format suitable for Kubespawner.

        Args:
            kubespawner_override (dict): Base configuration to override for this workspace.

        Returns:
            dict: A dictionary containing workspace configuration for Kubespawner.
        """
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
