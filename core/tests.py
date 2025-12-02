import io
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User, ServiceOrder as OrdemServico

class AuthTests(APITestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPassword123'
        }
        self.register_url = reverse('register')
        self.profile_url = reverse('auth-user-profile')

    def test_register_user_success(self):
        response = self.client.post(self.register_url, self.user_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')
        self.assertNotEqual(User.objects.get().password, 'StrongPassword123')

    def test_login_user_success(self):
        User.objects.create_user(**self.user_data)

        login_url = reverse('token_obtain_pair')

        response = self.client.post(login_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_get_user_profile_authenticated(self):
        user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], user.username)
        self.assertEqual(response.data['email'], user.email)

    def test_patch_user_profile(self):
        user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=user)

        new_data = {
            'first_name': 'Test',
            'last_name': 'User Updated'
        }
        response = self.client.patch(self.profile_url, new_data, format='json')

        user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User Updated')


class OrdemServicoTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='user',
            password='123',
            email='user@example.com'
        )
        self.admin = User.objects.create_user(
            username='admin',
            password='123',
            is_staff=True,
            email='admin@example.com'
        )

        self.client.force_authenticate(user=self.user)

        self.list_url = reverse('ordem-list')

        self.os1 = OrdemServico.objects.create(
            created_by=self.user,
            protocol="PROT-001",
            so_number="OS-001",
            recipient_name="Cliente Teste 1",
            description="Descrição teste 1 (Windows)",
            priority="high",
            status="open",
            cpf="401.853.320-99"
        )

        self.os2 = OrdemServico.objects.create(
            created_by=self.user,
            protocol="PROT-002",
            so_number="OS-002",
            recipient_name="Cliente Teste 2",
            description="Descrição teste 2 (Linux)",
            priority="low",
            status="completed",
            cpf="275.389.476-04"
        )

        self.os2.created_at = timezone.now() - timedelta(days=5)
        self.os2.save()

        self.detail_url = reverse('ordem-detail', kwargs={'pk': self.os1.pk})

    def test_list_ordens(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 2)

    def test_create_ordem_servico(self):
        data = {
            "protocol": "PROT-003",
            "so_number": "OS-003",
            "type": "installation",
            "status": "open",
            "provider": "technical",
            "priority": "medium",
            "recipient_name": "Cliente Novo",
            "cpf": "243.458.203-67",
            "description": "Instalar Office"
        }
        response = self.client.post(self.list_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OrdemServico.objects.count(), 3)
        new_os = OrdemServico.objects.get(protocol="PROT-003")
        self.assertEqual(new_os.created_by, self.user)

    def test_sla_fields_in_list(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        os_data = next(item for item in response.data['results'] if item['protocol'] == 'PROT-001')

        self.assertIn('due_date', os_data)
        self.assertIn('sla_status', os_data)
        self.assertIn('time_remaining_seconds', os_data)

        self.assertIn('cpf_anonimo', os_data)
        self.assertEqual(os_data['cpf_anonimo'], '401.***.***-99')
        self.assertNotIn('cpf', os_data)

    def test_sla_status_logic(self):
        response = self.client.get(reverse('ordem-detail', kwargs={'pk': self.os1.pk}))
        self.assertIn(response.data['sla_status'], ['on_time', 'nearing_due_date'])

        response = self.client.get(reverse('ordem-detail', kwargs={'pk': self.os2.pk}))
        self.assertEqual(response.data['sla_status'], 'on_time')

        self.os1.created_at = timezone.now() - timedelta(hours=30)
        self.os1.save()
        response = self.client.get(reverse('ordem-detail', kwargs={'pk': self.os1.pk}))
        self.assertEqual(response.data['sla_status'], 'overdue')


    def test_filter_by_status(self):
        response = self.client.get(self.list_url + '?status=open')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['protocol'], 'PROT-001')

    def test_search_by_description(self):
        response = self.client.get(self.list_url + '?search=windows')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['protocol'], 'PROT-001')

    def test_ordering_by_created_at(self):
        response = self.client.get(self.list_url + '?ordering=-criado_em')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['protocol'], 'PROT-001')

    def test_patch_ordem_servico(self):
        data = {'status': 'in_progress', 'description': 'Atualizado'}
        response = self.client.patch(self.detail_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')
        self.assertEqual(response.data['description'], 'Atualizado')

        self.os1.refresh_from_db()
        self.assertEqual(self.os1.status, 'in_progress')

    def test_delete_ordem_servico(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(OrdemServico.objects.count(), 1)

class CSVImportTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='user',
            password='123',
            is_staff=False,
            email='csvuser@example.com'
        )
        self.admin = User.objects.create_user(
            username='admin',
            password='123',
            is_staff=True,
            email='csvadmin@example.com'
        )
        self.import_url = reverse('ordem-import-csv')

        self.csv_content = (
            "protocol,so_number,type,status,recipient_name,cpf,provider,priority,description\n"
            "PROT-100,OS-100,administrative,open,CSV 1,275.351.678-29,technical,low,Desc 1\n"
            "PROT-101,OS-101,installation,in_progress,CSV 2,908.089.892-94,specialized,high,Desc 2\n"
        )
        self.csv_file = io.StringIO(self.csv_content)
        self.csv_file.name = "test.csv"

    def test_csv_import_admin_success(self):
        self.client.force_authenticate(user=self.admin)

        self.csv_file.seek(0)

        response = self.client.post(
            self.import_url,
            {'file': self.csv_file},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], "Importado com sucesso 2 ordens de serviço.")
        self.assertEqual(OrdemServico.objects.count(), 2)
        self.assertEqual(OrdemServico.objects.first().created_by, self.admin)

    def test_csv_import_invalid_data(self):
        self.client.force_authenticate(user=self.admin)

        invalid_csv_content = (
            "protocol,so_number,type,status,recipient_name,cpf,provider,priority,description\n"
            "PROT-100,OS-100,admin,open,CSV 1,111.111.111-11,tech,prioridade_invalida,Desc 1\n"
        )
        invalid_file = io.StringIO(invalid_csv_content)
        invalid_file.name = "invalid.csv"

        response = self.client.post(
            self.import_url,
            {"file": invalid_file},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("errors", response.data)

        error_entry = response.data["errors"][0]

        self.assertIn("type", error_entry)
        self.assertIn("provider", error_entry)
        self.assertIn("priority", error_entry)

        self.assertEqual(
            str(error_entry["type"][0]),
            '"admin" is not a valid choice.'
        )
        self.assertEqual(
            str(error_entry["provider"][0]),
            '"tech" is not a valid choice.'
        )
        self.assertEqual(
            str(error_entry["priority"][0]),
            '"prioridade_invalida" is not a valid choice.'
        )
