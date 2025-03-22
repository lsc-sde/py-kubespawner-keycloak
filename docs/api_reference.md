# API Reference

## KeycloakRequester

The `KeycloakRequester` class handles authentication and API requests to the Keycloak server.

### Constructor

```python
KeycloakRequester(
    base_url: str,
    token_url: str,
    client_id: str,
    client_secret: str,
    jwt_token: str = ""
)
```

Parameters:
- `base_url`: Base URL of the Keycloak API
- `token_url`: URL for obtaining access tokens
- `client_id`: Keycloak client ID
- `client_secret`: Keycloak client secret
- `jwt_token`: (Optional) Existing JWT token

### Methods

#### get_access_token

```python
get_access_token() -> str
```

Retrieves an access token from Keycloak using client credentials.

Returns:
- The access token string

Raises:
- `InvalidKeycloakResponseCodeException`: If Keycloak returns an error status code

#### query

```python
query(path: str) -> dict
```

Makes an authenticated API request to Keycloak.

Parameters:
- `path`: API endpoint path relative to the base URL

Returns:
- JSON response as a Python dictionary

Raises:
- `InvalidKeycloakResponseCodeException`: If Keycloak returns an error status code
- `requests.exceptions.JSONDecodeError`: If response cannot be decoded as JSON

## KubespawnerKeycloak

The `KubespawnerKeycloak` class integrates with JupyterHub's KubeSpawner to provide Keycloak-based workspace configuration.

### Constructor

```python
KubespawnerKeycloak(
    spawner: KubeSpawner,
    base_url: str,
    token_url: str,
    client_id: str,
    client_secret: str,
    environments_config: dict
)
```

Parameters:
- `spawner`: KubeSpawner instance
- `base_url`: Base URL of the Keycloak API
- `token_url`: URL for obtaining access tokens
- `client_id`: Keycloak client ID
- `client_secret`: Keycloak client secret
- `environments_config`: Dictionary of environment configurations

### Methods

#### get_groups

```python
get_groups() -> list
```

Retrieves all groups from Keycloak.

Returns:
- List of group objects

#### get_group

```python
get_group(group_id: str) -> Group
```

Retrieves a specific group by ID.

Parameters:
- `group_id`: Keycloak group ID

Returns:
- Group object

#### get_group_children

```python
get_group_children(group_id: str) -> dict
```

Retrieves all child groups for a given parent group ID.

Parameters:
- `group_id`: Parent group ID

Returns:
- Dictionary mapping group paths to group objects

#### get_permitted_workspaces

```python
get_permitted_workspaces() -> list
```

Determines which workspaces a user has access to based on their group memberships.

Returns:
- List of workspace profile configurations for KubeSpawner

Raises:
- `NoAssignedValidWorkspaces`: If user has no valid workspace assignments

## Exceptions

### InvalidKeycloakResponseCodeException

Raised when Keycloak API returns an error status code.

### NoAssignedValidWorkspaces

Raised when a user has no assigned or valid workspaces.
