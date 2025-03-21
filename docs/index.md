# KubeSpawner Keycloak

A library for integrating Keycloak authentication with KubeSpawner in JupyterHub.

## Overview

KubeSpawner Keycloak extends the functionality of KubeSpawner to support Keycloak authentication for JupyterHub deployments running on Kubernetes. This integration allows for secure authentication and authorization using Keycloak's identity management capabilities.

## Installation

```bash
pip install kubespawner-keycloak
```

## Features

- Seamless integration between JupyterHub's KubeSpawner and Keycloak
- Support for Keycloak roles and group-based access control
- Token management and refresh capabilities
- Configurable authentication flows

## Usage

Basic configuration in your `jupyterhub_config.py`:

```python
from kubespawner_keycloak import KeycloakAuthenticator

c.JupyterHub.authenticator_class = KeycloakAuthenticator
c.KeycloakAuthenticator.keycloak_url = 'https://keycloak.example.com/auth'
c.KeycloakAuthenticator.realm = 'jupyterhub'
c.KeycloakAuthenticator.client_id = 'jupyterhub-client'
c.KeycloakAuthenticator.client_secret = 'your-client-secret'
```

## Configuration Options

| Option          | Default | Description                      |
| --------------- | ------- | -------------------------------- |
| `keycloak_url`  | None    | URL to the Keycloak server       |
| `realm`         | None    | Keycloak realm name              |
| `client_id`     | None    | Client ID registered in Keycloak |
| `client_secret` | None    | Client secret for authentication |
| `token_timeout` | 300     | Token timeout in seconds         |

## Documentation

For more detailed documentation, please refer to the [official documentation](https://example.com/kubespawner-keycloak/docs).

## Contributing

Contributions are welcome! Please see our [contributing guidelines](CONTRIBUTING.md) for more details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.