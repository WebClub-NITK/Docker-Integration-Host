from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from hosts.models import Host, UserHostRole
from networks.models import Network
from unittest.mock import MagicMock, patch

User = get_user_model()

class NetworkTests(APITestCase):
    def setUp(self):
        # 1. Create Users
        self.admin = User.objects.create_superuser(username='admin', password='pass123')
        self.host_owner = User.objects.create_user(username='owner', password='pass123')
        self.viewer = User.objects.create_user(username='viewer', password='pass123')
        self.other_user = User.objects.create_user(username='other', password='pass123')

        # 2. Create Host
        self.host = Host.objects.create(
            alias='Production Server',
            ip_address='192.168.1.10',
            port=2375,
            created_by=self.admin
        )

        # 3. Assign roles to Host
        UserHostRole.objects.create(
            user=self.host_owner,
            host=self.host,
            role='HOST_OWNER',
            assigned_by=self.admin
        )
        UserHostRole.objects.create(
            user=self.viewer,
            host=self.host,
            role='VIEWER',
            assigned_by=self.admin
        )

        # 4. Create an existing Network
        self.network = Network.objects.create(
            host=self.host,
            created_by=self.admin,
            docker_network_id='mocked_docker_net_id_123',
            name='pre-existing-net',
            driver='bridge',
            subnet='172.20.0.0/16',
            gateway='172.20.0.1',
            internal=False,
            attachable=True
        )

        self.list_url = reverse('network-list-create', kwargs={'host_id': self.host.id})
        self.detail_url = reverse('network-detail', kwargs={'host_id': self.host.id, 'id': self.network.id})

    # --- LIST NETWORKS TESTS ---

    def test_authenticated_user_can_list_networks(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'pre-existing-net')

    def test_unassigned_user_cannot_list_networks(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_list_networks(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- CREATE NETWORK TESTS ---

    @patch('networks.docker_service.get_client')
    def test_admin_can_create_network(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_sdk_net = MagicMock()
        mock_sdk_net.id = 'newly_created_net_id_xyz'
        mock_client.networks.create.return_value = mock_sdk_net

        self.client.force_authenticate(user=self.admin)
        data = {
            'name': 'new-net',
            'driver': 'bridge',
            'subnet': '172.30.0.0/16',
            'gateway': '172.30.0.1',
            'internal': False,
            'attachable': True,
            'labels': {'env': 'prod'}
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'new-net')
        self.assertEqual(response.data['docker_network_id'], 'newly_created_net_id_xyz')
        self.assertTrue(Network.objects.filter(name='new-net').exists())

    @patch('networks.docker_service.get_client')
    def test_host_owner_can_create_network(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_sdk_net = MagicMock()
        mock_sdk_net.id = 'owner_created_net_id'
        mock_client.networks.create.return_value = mock_sdk_net

        self.client.force_authenticate(user=self.host_owner)
        data = {
            'name': 'owner-net',
            'driver': 'overlay',
            'internal': True
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Network.objects.filter(name='owner-net').exists())

    def test_viewer_cannot_create_network(self):
        self.client.force_authenticate(user=self.viewer)
        data = {
            'name': 'forbidden-net',
            'driver': 'bridge'
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- DETAIL NETWORK TESTS ---

    def test_can_retrieve_network_detail(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'pre-existing-net')

    # --- DELETE NETWORK TESTS ---

    @patch('networks.views.get_client')
    def test_admin_can_delete_network(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_sdk_net = MagicMock()
        mock_client.networks.get.return_value = mock_sdk_net

        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Network.objects.filter(id=self.network.id).exists())
        mock_sdk_net.remove.assert_called_once()

    def test_viewer_cannot_delete_network(self):
        self.client.force_authenticate(user=self.viewer)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Network.objects.filter(id=self.network.id).exists())

    # --- CONNECT CONTAINER TESTS ---

    @patch('networks.views.get_client')
    def test_admin_can_connect_container(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_sdk_net = MagicMock()
        mock_client.networks.get.return_value = mock_sdk_net

        self.client.force_authenticate(user=self.admin)
        url = reverse('network-connect', kwargs={'host_id': self.host.id, 'id': self.network.id})
        data = {
            'container_id': 'some_container_id_123',
            'aliases': ['web', 'frontend'],
            'ipv4_address': '172.18.0.5'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], f"Container some_container_id_123 connected to network {self.network.name}.")
        self.assertEqual(response.data['ipv4_address'], '172.18.0.5')
        mock_sdk_net.connect.assert_called_once_with('some_container_id_123', aliases=['web', 'frontend'], ipv4_address='172.18.0.5')

    def test_viewer_cannot_connect_container(self):
        self.client.force_authenticate(user=self.viewer)
        url = reverse('network-connect', kwargs={'host_id': self.host.id, 'id': self.network.id})
        data = {'container_id': 'some_container_id_123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- DISCONNECT CONTAINER TESTS ---

    @patch('networks.views.get_client')
    def test_admin_can_disconnect_container(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_sdk_net = MagicMock()
        mock_client.networks.get.return_value = mock_sdk_net

        self.client.force_authenticate(user=self.admin)
        url = reverse('network-disconnect', kwargs={'host_id': self.host.id, 'id': self.network.id})
        data = {'container_id': 'some_container_id_123', 'force': True}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], f"Container some_container_id_123 disconnected from network {self.network.name}.")
        mock_sdk_net.disconnect.assert_called_once_with('some_container_id_123', force=True)

    def test_viewer_cannot_disconnect_container(self):
        self.client.force_authenticate(user=self.viewer)
        url = reverse('network-disconnect', kwargs={'host_id': self.host.id, 'id': self.network.id})
        data = {'container_id': 'some_container_id_123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- INSPECT CONTAINER DETAIL TESTS ---

    @patch('networks.views.get_client')
    def test_can_retrieve_network_detail_with_options_and_containers(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_sdk_net = MagicMock()
        mock_sdk_net.attrs = {
            'Options': {'com.docker.network.bridge.name': 'docker1'},
            'Containers': {
                'container_id_abc': {
                    'Name': 'my-nginx',
                    'IPv4Address': '172.18.0.2/16',
                    'MacAddress': '02:42:ac:12:00:02'
                }
            }
        }
        mock_client.networks.get.return_value = mock_sdk_net

        self.client.force_authenticate(user=self.viewer)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['options'], {'com.docker.network.bridge.name': 'docker1'})
        self.assertIn('container_id_abc', response.data['containers'])
        container_data = response.data['containers']['container_id_abc']
        self.assertEqual(container_data['name'], 'my-nginx')
        self.assertEqual(container_data['ipv4_address'], '172.18.0.2')
        self.assertEqual(container_data['mac_address'], '02:42:ac:12:00:02')

    # --- PRUNE NETWORKS TESTS ---

    @patch('networks.views.get_client')
    def test_admin_can_prune_unused_networks(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.networks.prune.return_value = {
            'NetworksDeleted': ['pre-existing-net', 'another-unused-net']
        }

        # Create another network to test syncing with db
        Network.objects.create(
            host=self.host,
            created_by=self.admin,
            docker_network_id='mocked_docker_net_id_456',
            name='another-unused-net',
            driver='bridge'
        )

        self.client.force_authenticate(user=self.admin)
        url = reverse('network-prune', kwargs={'host_id': self.host.id})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['networks_deleted'], ['pre-existing-net', 'another-unused-net'])
        self.assertEqual(response.data['message'], "2 unused networks removed.")
        
        # Verify database is synced (both deleted networks should be removed)
        self.assertFalse(Network.objects.filter(name='pre-existing-net').exists())
        self.assertFalse(Network.objects.filter(name='another-unused-net').exists())

    def test_viewer_cannot_prune_unused_networks(self):
        self.client.force_authenticate(user=self.viewer)
        url = reverse('network-prune', kwargs={'host_id': self.host.id})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
