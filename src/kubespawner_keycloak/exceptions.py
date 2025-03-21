"""
Exceptions for the kubespawner-keycloak module.

This module contains custom exceptions that are raised by the kubespawner-keycloak
module when various error conditions are encountered during Keycloak group operations
and workspace management.
"""


class InvalidKeycloakGroupPath(Exception):
    """
    Exception raised when a Keycloak group path does not match the expected format.

    Raised when a group path does not begin with the expected parent group prefix.

    Args:
        group_name (str): The name of the group with an invalid path
        parent_group_name (str): The expected parent group name
    """

    def __init__(self, group_name, parent_group_name):
        self.group_name = group_name
        self.parent_group_name = parent_group_name
        self.message = (
            f"Group Path: {group_name} does not begin with /{parent_group_name}/"
        )
        super().__init__(self.message)


class InvalidKeycloakResponseCodeException(Exception):
    """
    Exception raised when a Keycloak API response code does not match the expected value.

    Args:
        received_code (int): The HTTP status code received from Keycloak
        expected_code (int, optional): The expected HTTP status code. Defaults to 200.
    """

    def __init__(self, received_code, expected_code=200):
        self.received_code = received_code
        self.expected_code = expected_code
        self.message = f"Expected Keycloak response of {expected_code} but received {received_code}"
        super().__init__(self.message)


class KeycloakGroupConversionException(Exception):
    """
    Exception raised when there's an error converting Keycloak group definitions.

    This exception is typically raised when a group definition cannot be properly
    parsed or processed.

    Args:
        group_definition (dict): The Keycloak group definition that failed conversion
        inner_message (str): Detailed message describing the conversion error
    """

    def __init__(self, group_definition, inner_message):
        self.group_definition = group_definition
        self.message = f"Error Converting the group definition: {inner_message}"
        super().__init__(self.message)


class KeycloakGroupNotFoundException(Exception):
    """
    Exception raised when a requested Keycloak group cannot be found.

    Args:
        group_name (str): The name of the group that couldn't be found
    """

    def __init__(self, group_name):
        self.group_name = group_name
        self.message = f"Could not find the group: {group_name}"
        super().__init__(self.message)


class NoAssignedValidWorkspaces(Exception):
    """
    Exception raised when a user has no valid workspaces assigned.

    This exception is raised during workspace validation when a user
    doesn't have access to any workspaces.

    Args:
        user (str): The username of the user with no valid workspaces
    """

    def __init__(self, user):
        self.user = user
        self.message = f"User {user} does not have any valid workspaces assigned"
        super().__init__(self.message)
