# Usage Examples

## Basic Integration

This example shows how to integrate KubespawnerKeycloak with JupyterHub in a typical deployment:

```python
from kubespawner_keycloak import KubespawnerKeycloak

# Environment configurations
environments_config = {
    "jupyter_default": {
        "image": "jupyter/datascience-notebook:latest",
        "resources": {
            "limits": {
                "memory": "2G",
                "cpu": "1"
            }
        }
    },
    "jupyter_advanced": {
        "image": "jupyter/tensorflow-notebook:latest",
        "resources": {
            "limits": {
                "memory": "8G",
                "cpu": "4",
                "nvidia.com/gpu": "1"
            }
        }
    }
}

def pre_spawn_hook(spawner):
    keycloak = KubespawnerKeycloak(
        spawner=spawner,
        base_url='https://keycloak.example.org/auth/admin/realms/jupyterhub',
        token_url='https://keycloak.example.org/auth/realms/jupyterhub/protocol/openid-connect/token',
        client_id='jupyterhub-admin',
        client_secret='your-admin-client-secret',
        environments_config=environments_config
    )
    
    try:
        permitted_workspaces = keycloak.get_permitted_workspaces()
        spawner.profile_list = permitted_workspaces
    except NoAssignedValidWorkspaces:
        # Handle case where user has no workspaces
        spawner.profile_list = [{
            "display_name": "Default Environment",
            "description": "Basic Jupyter environment",
            "kubespawner_override": {
                "image": "jupyter/minimal-notebook:latest",
                "cpu_limit": 0.5,
                "mem_limit": "1G"
            }
        }]

c.KubeSpawner.pre_spawn_hook = pre_spawn_hook
```

## Advanced Configuration with Time-Limited Access

This example shows how to use time-limited workspaces with custom resource configurations:

```python
from kubespawner_keycloak import KubespawnerKeycloak, NoAssignedValidWorkspaces
from datetime import datetime

# Environment configurations with additional parameters
environments_config = {
    "jupyter_default": {
        "image": "jupyter/datascience-notebook:latest",
        "resources": {
            "limits": {
                "memory": "2G",
                "cpu": "1"
            }
        },
        "storage_capacity": "10Gi"
    },
    "jupyter_advanced": {
        "image": "jupyter/tensorflow-notebook:latest",
        "resources": {
            "limits": {
                "memory": "8G",
                "cpu": "4",
                "nvidia.com/gpu": "1"
            }
        },
        "storage_capacity": "50Gi",
        "extra_mounts": [
            {
                "name": "datasets",
                "mountPath": "/home/jovyan/datasets",
                "readonly": True,
                "claim_name": "shared-datasets-pvc"
            }
        ]
    }
}

def pre_spawn_hook(spawner):
    keycloak = KubespawnerKeycloak(
        spawner=spawner,
        base_url='https://keycloak.example.org/auth/admin/realms/jupyterhub',
        token_url='https://keycloak.example.org/auth/realms/jupyterhub/protocol/openid-connect/token',
        client_id='jupyterhub-admin',
        client_secret='your-admin-client-secret',
        environments_config=environments_config
    )
    
    try:
        permitted_workspaces = keycloak.get_permitted_workspaces()
        
        # Add current date to each workspace for tracking
        now = datetime.now().isoformat()
        for workspace in permitted_workspaces:
            workspace["last_selected"] = now
            
            # Add any custom logic for workspace configuration
            if "gpu" in workspace["display_name"].lower():
                workspace["kubespawner_override"]["extra_labels"]["requires_gpu"] = "true"
            
        spawner.profile_list = permitted_workspaces
    except NoAssignedValidWorkspaces:
        # Redirect user to request access page
        from tornado.web import HTTPError
        raise HTTPError(403, "You do not have access to any workspaces. Please request access.")

c.KubeSpawner.pre_spawn_hook = pre_spawn_hook
```

## Keycloak Group Structure

The expected Keycloak group structure for workspaces:

```
/jupyter-workspaces
├── Research Project A Workspace
│   attributes:
│   ├── workspace.xlscsde.nhs.uk/environment: jupyter_advanced
│   ├── workspace.xlscsde.nhs.uk/startDate: 2023-01-01
│   ├── workspace.xlscsde.nhs.uk/endDate: 2023-12-31
│   └── workspace.xlscsde.nhs.uk/description: Research environment for Project A
├── Generic Data Analysis Workspace
│   attributes:
│   ├── workspace.xlscsde.nhs.uk/environment: jupyter_default
│   ├── workspace.xlscsde.nhs.uk/startDate: 2023-01-01
│   ├── workspace.xlscsde.nhs.uk/endDate: 2024-12-31
│   └── workspace.xlscsde.nhs.uk/description: General data analysis environment
└── ML Research Workspace
    attributes:
    ├── workspace.xlscsde.nhs.uk/environment: jupyter_advanced
    ├── workspace.xlscsde.nhs.uk/startDate: 2023-06-01
    ├── workspace.xlscsde.nhs.uk/endDate: 2023-12-31
    └── workspace.xlscsde.nhs.uk/description: Machine learning research environment
```

To assign a user to a workspace, add them to the corresponding Keycloak group.
