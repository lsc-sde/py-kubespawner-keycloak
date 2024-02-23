from kubespawner.spawner import KubeSpawner
from kubernetes_asyncio import client
from .objects import WorkspaceVolumeStatus
from kubernetes_asyncio.client.models import (
    V1ObjectMeta,
    V1Pod,
    V1Volume,
    V1VolumeMount,
    V1PersistentVolumeClaim,
    V1PersistentVolumeClaimSpec,
    V1PersistentVolumeClaimVolumeSource,
)

class VolumeManager:
    def __init__(self, spawner: KubeSpawner, k8s_api : client.ApiClient):
        self.spawner = spawner
        self.v1_api = client.CoreV1Api(k8s_api)
        
    async def get_workspace_volume_status(self, workspace_name: str, namespace: str):
        name = f"jupyter-{workspace_name}"
        exists = True
        try:
            self.spawner.log.info(f"Checking if PVC {name} on {namespace} exists")
            response = await self.v1_api.read_namespaced_persistent_volume_claim(name, namespace)
            self.spawner.log.info(f"response: {response}")

        except client.exceptions.ApiException as e:
            if e.status == 404:
                exists = False
            else:
                raise e
        
        return WorkspaceVolumeStatus(name, namespace, exists)

    async def create_workspace_volume_if_not_exists(self, workspace_name: str, namespace: str):
        status = await self.get_workspace_volume_status(workspace_name, namespace)
        if not status.exists:
            self.spawner.log.info(f"PVC {status.name} on {status.namespace} does not exist.")
            
            pvc = V1PersistentVolumeClaim(
                metadata = V1ObjectMeta(
                    name=status.name,
                    namespace= namespace,
                    labels={
                        "workspace.xlscsde.nhs.uk/workspace" : workspace_name,
                        "workspace.xlscsde.nhs.uk/storageType" : "workspace",
                    }
                ),
                spec=V1PersistentVolumeClaimSpec(
                    storage_class_name="jupyter-default",
                    access_modes=["ReadWriteMany"],
                    resources= {
                        "requests": { 
                            "storage": "10Gi"
                        }
                    }
                )
            )
            await self.v1_api.create_namespaced_persistent_volume_claim(namespace, pvc)
            status.exists = True
        else: 
            self.spawner.log.info(f"PVC {status.name} on {status.namespace} already exists.")

        return status
    
    async def mount_volume(self, pod: V1Pod, storage_name : str, namespace: str, read_only : bool = False):
        self.spawner.log.info(f"Attempting to mount {storage_name} on {namespace}...")
        storage = await self.create_workspace_volume_if_not_exists(storage_name, namespace)

        if storage:
            volume = V1Volume(
                name = storage_name,
                persistent_volume_claim=V1PersistentVolumeClaimVolumeSource(
                    claim_name=storage.name
                )
            )

            mount_path= f"/home/jovyan/{storage_name}"
            volume_mount = V1VolumeMount(
                name = storage_name,
                mount_path= mount_path,
                read_only = read_only
            )
            pod.spec.volumes.append(volume)
            pod.spec.containers[0].volume_mounts.append(volume_mount)

            self.spawner.log.info(f"Successfully mounted {storage.name} to {mount_path}.")
