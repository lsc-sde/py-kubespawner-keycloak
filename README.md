# KubeSpawner-Keycloak

A JupyterHub KubeSpawner extension that integrates with Keycloak for authentication and workspace permissions management.

## Overview

This package provides a seamless integration between JupyterHub's KubeSpawner and Keycloak authentication. It allows JupyterHub to retrieve user workspace permissions from Keycloak and dynamically configure available workspaces based on those permissions.

## Features

- Keycloak authentication integration
- Dynamic workspace configuration based on user group membership
- Attribute-based access controls for Jupyter environments
- Support for workspace-specific environment configurations

## Installation

```bash
pip install kubespawner-keycloak
```

## Configuration

In your JupyterHub configuration file (`jupyterhub_config.py`), add:

```python
from kubespawner_keycloak import KubespawnerKeycloak

c.JupyterHub.authenticator_class = 'oauthenticator.generic.GenericOAuthenticator'
c.GenericOAuthenticator.oauth_callback_url = 'https://your-jupyterhub-domain/hub/oauth_callback'
c.GenericOAuthenticator.client_id = 'your-keycloak-client-id'
c.GenericOAuthenticator.client_secret = 'your-keycloak-client-secret'
c.GenericOAuthenticator.login_service = 'Keycloak'
c.GenericOAuthenticator.username_key = 'preferred_username'
c.GenericOAuthenticator.authorize_url = 'https://your-keycloak-domain/auth/realms/your-realm/protocol/openid-connect/auth'
c.GenericOAuthenticator.token_url = 'https://your-keycloak-domain/auth/realms/your-realm/protocol/openid-connect/token'
c.GenericOAuthenticator.userdata_url = 'https://your-keycloak-domain/auth/realms/your-realm/protocol/openid-connect/userinfo'

# Environment configurations
environments_config = {
    "jupyter_default": {
        "image": "jupyter/datascience-notebook:latest"
    },
    "jupyter_advanced": {
        "image": "jupyter/datascience-notebook:latest",
        "resources": {
            "limits": {
                "memory": "4G",
                "cpu": "2"
            }
        }
    }
}

# Configure KubespawnerKeycloak
def pre_spawn_hook(spawner):
    keycloak = KubespawnerKeycloak(
        spawner=spawner,
        base_url='https://your-keycloak-domain/auth/admin/realms/your-realm',
        token_url='https://your-keycloak-domain/auth/realms/your-realm/protocol/openid-connect/token',
        client_id='admin-cli',
        client_secret='your-admin-client-secret',
        environments_config=environments_config
    )
    
    permitted_workspaces = keycloak.get_permitted_workspaces()
    spawner.profile_list = permitted_workspaces

c.KubeSpawner.pre_spawn_hook = pre_spawn_hook
```

## Keycloak Configuration

In Keycloak, set up:

1. A client for JupyterHub authentication
2. A separate admin client for querying group information
3. Groups with the path `/jupyter-workspaces/[Workspace Name]`
4. Group attributes with the format `workspace.xlscsde.nhs.uk/[attribute-name]`

Required group attributes:
- `workspace.xlscsde.nhs.uk/environment`: The environment type
- `workspace.xlscsde.nhs.uk/startDate`: Start date for workspace access
- `workspace.xlscsde.nhs.uk/endDate`: End date for workspace access
- `workspace.xlscsde.nhs.uk/description`: Description of the workspace

## License

[Insert your license information here]