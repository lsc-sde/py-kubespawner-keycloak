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
