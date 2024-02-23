import asyncio
from jupyterhub.objects import Hub, Server
from KubespawnerKeycloak import KeycloakRequester, KubespawnerKeycloak, InvalidKeycloakResponseCodeException, NoAssignedValidWorkspaces
from kubespawner import KubeSpawner
import pytest
import requests
from unittest.mock import Mock

class TestKeycloakRequester:
    base_url : str = "http://test.com"
    def test_not_found(self, requests_mock):
        url : str = f"{self.base_url}/groups?populateHierarchy=true"
        requests_mock.get(url, text='<testing></testing>', status_code = 404)
        requester = KeycloakRequester(self.base_url, "", "")
        with pytest.raises(InvalidKeycloakResponseCodeException):
            requester.query("/groups?populateHierarchy=true")
    
    def test_server_error(self, requests_mock):
        url : str = f"{self.base_url}/groups?populateHierarchy=true"
        requests_mock.get(url, text='<testing></testing>', status_code = 500)
        requester = KeycloakRequester(self.base_url, "", "")
        with pytest.raises(InvalidKeycloakResponseCodeException):
            requester.query("/groups?populateHierarchy=true")

    def test_invalid_response(self, requests_mock):
        url : str = f"{self.base_url}/groups?populateHierarchy=true"
        requests_mock.get(url, text='<testing></testing>', status_code = 200)
        requester = KeycloakRequester(self.base_url, "", "")
        with pytest.raises(requests.exceptions.JSONDecodeError):
            requester.query("/groups?populateHierarchy=true")

    def test_get_groups(self, requests_mock):
        url : str = f"{self.base_url}/groups?populateHierarchy=true"
        data = '[{"id": "429c803a-a033-4e1e-8aea-73b92fd43003","name": "jupyter-workspaces","path": "/jupyter-workspaces","subGroupCount": 2, "access": { "view": true, "viewMembers": true, "manageMembers": false, "manage": false, "manageMembership": false } }, { "id": "0239d876-a497-476d-96c8-96bde8d9f718", "name": "some-other-group", "path": "/some-other-group","subGroupCount": 0,"access": {"view": true, "viewMembers": true, "manageMembers": false,"manage": false,"manageMembership": false }}]'
        requests_mock.get(url, text=data, status_code = 200)
        requester = KeycloakRequester(self.base_url, "", "")
        result = requester.query("/groups?populateHierarchy=true")
        assert len(result) == 2
        
    def test_get_children(self, requests_mock):
        url : str = f"{self.base_url}/groups/429c803a-a033-4e1e-8aea-73b92fd43003/children"
        data = '[{"id": "79cdf13c-a6bc-46cd-8a5d-1281b0fe8e53","name": "Colorectal Cancer Research Group Workspace","path": "/jupyter-workspaces/Colorectal Cancer Research Group Workspace","parentId": "429c803a-a033-4e1e-8aea-73b92fd43003","subGroupCount": 0,"attributes": {"workspace.xlscsde.nhs.uk/environment": ["jupyter_advanced"],"workspace.xlscsde.nhs.uk/startDate": ["2022-01-01"],"workspace.xlscsde.nhs.uk/endDate": ["2030-01-01"],"workspace.xlscsde.nhs.uk/description": ["An example workspace for the testing of using keycloak groups"]},"access": {"view": true,"viewMembers": true,"manageMembers": false,"manage": false,"manageMembership": false}},{"id": "a6fdb60b-f11d-4c59-bdf3-e03fac24b6ab","name": "Default Generic Workspace","path": "/jupyter-workspaces/Default Generic Workspace","parentId": "429c803a-a033-4e1e-8aea-73b92fd43003","subGroupCount": 0,"attributes": {"workspace.xlscsde.nhs.uk/startDate": ["2022-01-01"],"workspace.xlscsde.nhs.uk/environment": ["jupyter_default"],"workspace.xlscsde.nhs.uk/endDate": ["2030-01-01"],"workspace.xlscsde.nhs.uk/description": ["Basic environment for testing with Python R and Julia."]},"access": {"view": true,"viewMembers": true,"manageMembers": false,"manage": false,"manageMembership": false}}]'
        requests_mock.get(url, text=data, status_code = 200)
        requester = KeycloakRequester(self.base_url, "", "")
        result = requester.query("/groups/429c803a-a033-4e1e-8aea-73b92fd43003/children")
        assert len(result) == 2

class TestKubespawnerKeycloak:
    base_url : str = "http://test.com"
    
    @pytest.mark.asyncio
    async def test_get_groups(self, requests_mock):
        self.mock_get_groups(requests_mock)
        spawner = await self.create_spawner([])
        keycloak = KubespawnerKeycloak(spawner = spawner, base_url = self.base_url, environments_config = self.get_environments_config(), access_token="")
        result = keycloak.get_groups()
        assert len(result) == 2
        
    @pytest.mark.asyncio
    async def test_get_group(self, requests_mock):
        self.mock_get_group(requests_mock)
        spawner = await self.create_spawner([])
        keycloak = KubespawnerKeycloak(spawner = spawner, base_url = self.base_url, environments_config = self.get_environments_config(), access_token="")
        result = keycloak.get_group("a6fdb60b-f11d-4c59-bdf3-e03fac24b6ab")
        assert "a6fdb60b-f11d-4c59-bdf3-e03fac24b6ab" == result.id

    @pytest.mark.asyncio
    async def test_get_child_group(self, requests_mock):
        self.mock_get_child_groups(requests_mock)
        spawner = await self.create_spawner([])
        keycloak = KubespawnerKeycloak(spawner = spawner, base_url = self.base_url, environments_config = self.get_environments_config(), access_token="")
        result = keycloak.get_group_children("429c803a-a033-4e1e-8aea-73b92fd43003")
        assert 2 == len(result)
        assert "/jupyter-workspaces/colorectal cancer research group workspace" in result.keys()
        assert "/jupyter-workspaces/default generic workspace" in result.keys()
        assert "79cdf13c-a6bc-46cd-8a5d-1281b0fe8e53" == result["/jupyter-workspaces/colorectal cancer research group workspace"].id

    @pytest.mark.asyncio
    async def test_get_workspaces(self, requests_mock):
        self.mock_get_groups(requests_mock)
        self.mock_get_child_groups(requests_mock)
        self.mock_get_group(requests_mock)
        groups = ["/jupyter-workspaces/Colorectal Cancer Research Group Workspace"]
        spawner = await self.create_spawner(groups)
        keycloak = KubespawnerKeycloak(spawner = spawner, base_url = self.base_url, environments_config = self.get_environments_config(), access_token="")
        environments_config = {}
        environments_config["jupyter_advanced"] = {}
        environments_config["jupyter_advanced"]["image"] = "jupyter/datascience-notebook:latest"
        environments_config["jupyter_default"] = {}
        environments_config["jupyter_default"]["image"] = "jupyter/datascience-notebook:latest"
        permitted_workspaces = keycloak.get_permitted_workspaces()
        print(f"permitted_workspaces = {permitted_workspaces}")
        
        assert 1 == len(permitted_workspaces)
        assert "Colorectal Cancer Research Group Workspace" == permitted_workspaces[0].get("display_name")
        assert "colorectal-cancer-research-group-workspace" == permitted_workspaces[0]["kubespawner_override"]["extra_labels"]["workspace"]

    @pytest.mark.asyncio
    async def test_get_no_workspaces(self, requests_mock):
        self.mock_get_groups(requests_mock)
        self.mock_get_child_groups(requests_mock)
        self.mock_get_group(requests_mock)
        groups = []
        spawner = await self.create_spawner(groups)
        keycloak = KubespawnerKeycloak(spawner = spawner, base_url = self.base_url, environments_config = self.get_environments_config(), access_token="")
        
        with pytest.raises(NoAssignedValidWorkspaces):
            permitted_workspaces = keycloak.get_permitted_workspaces()
            print(f"permitted_workspaces = {permitted_workspaces}")
        
    def get_environments_config(self):
        environments_config = {}
        environments_config["jupyter_advanced"] = {}
        environments_config["jupyter_advanced"]["image"] = "jupyter/datascience-notebook:latest"
        environments_config["jupyter_default"] = {}
        environments_config["jupyter_default"]["image"] = "jupyter/datascience-notebook:latest"
        return environments_config

    async def create_spawner(self, groups):
        spawner = KubeSpawner(user = MockUser(), hub = Hub())
        spawner.oauth_user = {}
        spawner.oauth_user["realm_groups"] = groups
        return spawner

    def mock_get_child_groups(self, requests_mock):
        url : str = f"{self.base_url}/groups/429c803a-a033-4e1e-8aea-73b92fd43003/children"
        data = '[{"id": "79cdf13c-a6bc-46cd-8a5d-1281b0fe8e53","name": "Colorectal Cancer Research Group Workspace","path": "/jupyter-workspaces/Colorectal Cancer Research Group Workspace","parentId": "429c803a-a033-4e1e-8aea-73b92fd43003","subGroupCount": 0,"attributes": {"workspace.xlscsde.nhs.uk/environment": ["jupyter_advanced"],"workspace.xlscsde.nhs.uk/startDate": ["2022-01-01"],"workspace.xlscsde.nhs.uk/endDate": ["2030-01-01"],"workspace.xlscsde.nhs.uk/description": ["An example workspace for the testing of using keycloak groups"]},"access": {"view": true,"viewMembers": true,"manageMembers": false,"manage": false,"manageMembership": false}},{"id": "a6fdb60b-f11d-4c59-bdf3-e03fac24b6ab","name": "Default Generic Workspace","path": "/jupyter-workspaces/Default Generic Workspace","parentId": "429c803a-a033-4e1e-8aea-73b92fd43003","subGroupCount": 0,"attributes": {"workspace.xlscsde.nhs.uk/startDate": ["2022-01-01"],"workspace.xlscsde.nhs.uk/environment": ["jupyter_default"],"workspace.xlscsde.nhs.uk/endDate": ["2030-01-01"],"workspace.xlscsde.nhs.uk/description": ["Basic environment for testing with Python R and Julia."]},"access": {"view": true,"viewMembers": true,"manageMembers": false,"manage": false,"manageMembership": false}}]'
        requests_mock.get(url, text=data, status_code = 200)

    def mock_get_groups(self, requests_mock):
        url : str = f"{self.base_url}/groups?populateHierarchy=true"
        data = '[{"id": "429c803a-a033-4e1e-8aea-73b92fd43003","name": "jupyter-workspaces","path": "/jupyter-workspaces","subGroupCount": 2, "access": { "view": true, "viewMembers": true, "manageMembers": false, "manage": false, "manageMembership": false } }, { "id": "0239d876-a497-476d-96c8-96bde8d9f718", "name": "some-other-group", "path": "/some-other-group","subGroupCount": 0,"access": {"view": true, "viewMembers": true, "manageMembers": false,"manage": false,"manageMembership": false }}]'
        requests_mock.get(url, text=data, status_code = 200)

    def mock_get_group(self, requests_mock):
        url : str = f"{self.base_url}/groups/a6fdb60b-f11d-4c59-bdf3-e03fac24b6ab"
        data = '{ "id": "a6fdb60b-f11d-4c59-bdf3-e03fac24b6ab", "name": "Default Generic Workspace", "path": "/jupyter-workspaces/Default Generic Workspace", "parentId": "429c803a-a033-4e1e-8aea-73b92fd43003", "subGroupCount": 0, "attributes": { "workspace.xlscsde.nhs.uk/startDate": [ "2022-01-01" ], "workspace.xlscsde.nhs.uk/environment": [ "jupyter_default" ], "workspace.xlscsde.nhs.uk/endDate": [ "2030-01-01" ], "workspace.xlscsde.nhs.uk/description": [ "Basic environment for testing with Python R and Julia." ] }, "access": { "view": true, "viewMembers": true, "manageMembers": false, "manage": false, "manageMembership": false } }'
        requests_mock.get(url, text=data, status_code = 200)
    
    
class MockUser(Mock):
    name = 'fake'
    server = Server()

    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def escaped_name(self):
        return self.name

    @property
    def url(self):
        return self.server.url