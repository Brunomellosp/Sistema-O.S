import io
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User, ServiceOrder as OrdemServico

class AuthTests(APITestCase):
    """
    Testes para Autenticação (Registro, Login, Perfil).
    Esta é a base, vamos manter por enquanto.
    """

    def setUp(self):
        # Dados de um usuário de teste
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPassword123'
        }
        # URL do endpoint de registro
        self.register_url = reverse('register')
        # URL do endpoint de perfil
        self.profile_url = reverse('auth-user-profile')

    def test_register_user_success(self):
        """Testa o registro de usuário com sucesso."""
        response = self.client.post(self.register_url, self.user_data, format='json')
        
        # Verifica se o status code é 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verifica se o usuário foi realmente criado no banco
        self.assertEqual(User.objects.count(), 1)
        # Verifica se o username está correto
        self.assertEqual(User.objects.get().username, 'testuser')
        # Verifica se a senha foi hasheada (não está em texto plano)
        self.assertNotEqual(User.objects.get().password, 'StrongPassword123')

    def test_login_user_success(self):
        """Testa o login de usuário com sucesso."""
        # Primeiro, cria o usuário
        User.objects.create_user(**self.user_data)
        
        # URL do endpoint de login (SimpleJWT)
        login_url = reverse('token_obtain_pair')
        
        # Tenta fazer login
        response = self.client.post(login_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }, format='json')
        
        # Verifica se o status code é 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verifica se os tokens 'access' e 'refresh' foram retornados
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_get_user_profile_authenticated(self):
        """Testa se um usuário logado consegue ver seu perfil."""
        user = User.objects.create_user(**self.user_data)
        # Força a autenticação (login)
        self.client.force_authenticate(user=user)
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], user.username)
        self.assertEqual(response.data['email'], user.email)

    #Vamos comentar este por enquanto para simplificar
    def test_patch_user_profile(self):
        """Testa se o usuário logado consegue atualizar seu perfil."""
        user = User.objects.create_user(**self.user_data)
        self.client.force_authenticate(user=user)
        
        new_data = {
            'first_name': 'Test',
            'last_name': 'User Updated'
        }
        response = self.client.patch(self.profile_url, new_data, format='json')
        
        # Recarrega o usuário do banco de dados
        user.refresh_from_db()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User Updated')


class OrdemServicoTests(APITestCase):
    """Testes para o CRUD e funcionalidades das Ordens de Serviço"""

    def setUp(self):
        # Cria um usuário comum e um admin com emails únicos
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
        
        # Autentica o usuário comum para a maioria dos testes
        self.client.force_authenticate(user=self.user)
        
        # URLs
        self.list_url = reverse('ordem-list')
        
        # Cria uma OS de teste (High Priority)
        self.os1 = OrdemServico.objects.create(
            created_by=self.user,
            protocol="PROT-001",
            so_number="OS-001",
            recipient_name="Cliente Teste 1",
            description="Descrição teste 1 (Windows)",
            priority="high",
            status="open",
            cpf="111.111.111-11"
        )

        # Cria uma OS de teste (Low Priority, antiga) - COMENTADO
        self.os2 = OrdemServico.objects.create(
            created_by=self.user,
            protocol="PROT-002",
            so_number="OS-002",
            recipient_name="Cliente Teste 2",
            description="Descrição teste 2 (Linux)",
            priority="low",
            status="completed",
            cpf="222.222.222-22"
        )

        # Altera a data da OS 2 para ser antiga
        self.os2.created_at = timezone.now() - timedelta(days=5)
        self.os2.save()
        
        self.detail_url = reverse('ordem-detail', kwargs={'pk': self.os1.pk})

    def test_list_ordens(self):
        """Testa a listagem de OS (básico)."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verifica se a resposta tem a estrutura de paginação (DRF Padrão)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 1)

    def test_create_ordem_servico(self):
        """Testa a criação de uma nova OS."""
        data = {
            "protocol": "PROT-003",
            "so_number": "OS-003",
            "type": "installation",
            "status": "open",
            "provider": "technical",
            "priority": "medium",
            "recipient_name": "Cliente Novo",
            "cpf": "333.333.333-33",
            "description": "Instalar Office"
        }
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OrdemServico.objects.count(), 2) # Agora são 2 (1 do setUp + 1 novo)
        # Verifica se o 'criado_por' foi salvo corretamente
        new_os = OrdemServico.objects.get(protocol="PROT-003")
        self.assertEqual(new_os.created_by, self.user)

    # --- TESTES AVANÇADOS COMENTADOS PARA FOCAR NOS BÁSICOS PRIMEIRO ---

    def test_sla_fields_in_list(self):
        """Testa se os campos de SLA e CPF anonimizado estão na resposta."""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ordenação padrão pode não ser garantida, então buscamos a OS certa
        os_data = next(item for item in response.data['results'] if item['protocol'] == 'PROT-001')

        # Verifica campos de SLA
        self.assertIn('due_date', os_data)
        self.assertIn('sla_status', os_data)
        self.assertIn('time_remaining_seconds', os_data)
        
        # Verifica anonimização do CPF
        self.assertIn('cpf_anonimo', os_data)
        self.assertEqual(os_data['cpf_anonimo'], '111.***.***-11')
        self.assertNotIn('cpf', os_data) # O CPF original não deve estar

    def test_sla_status_logic(self):
        """Testa a lógica de status do SLA (overdue, on_time)."""
        # A OS 1 (high priority) vence em 24h, deve estar 'on_time' ou 'nearing_due_date'
        response = self.client.get(reverse('ordem-detail', kwargs={'pk': self.os1.pk}))
        self.assertIn(response.data['sla_status'], ['on_time', 'nearing_due_date'])
        
        # A OS 2 (completed) deve estar 'on_time'
        response = self.client.get(reverse('ordem-detail', kwargs={'pk': self.os2.pk}))
        self.assertEqual(response.data['sla_status'], 'on_time')
        
        # Força a OS 1 a estar vencida (cria ela 30h atrás)
        self.os1.created_at = timezone.now() - timedelta(hours=30)
        self.os1.save()
        response = self.client.get(reverse('ordem-detail', kwargs={'pk': self.os1.pk}))
        self.assertEqual(response.data['sla_status'], 'overdue')


    def test_filter_by_status(self):
        """Testa o filtro por status."""
        response = self.client.get(self.list_url + '?status=open')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['protocol'], 'PROT-001')

    def test_search_by_description(self):
        """Testa a busca por texto na descrição."""
        response = self.client.get(self.list_url + '?search=windows')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['protocol'], 'PROT-001')

    def test_ordering_by_created_at(self):
        """Testa a ordenação por data de criação (mais novas primeiro)."""
        response = self.client.get(self.list_url + '?ordering=-criado_em')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # A OS 1 (mais nova) deve vir primeiro
        self.assertEqual(response.data['results'][0]['protocol'], 'PROT-001')

    def test_patch_ordem_servico(self):
        """Testa a atualização (PATCH) de uma OS."""
        data = {'status': 'in_progress', 'description': 'Atualizado'}
        response = self.client.patch(self.detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')
        self.assertEqual(response.data['description'], 'Atualizado')
        
        # Verifica no banco
        self.os1.refresh_from_db()
        self.assertEqual(self.os1.status, 'in_progress')

    def test_delete_ordem_servico(self):
        """Testa o delete de uma OS."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(OrdemServico.objects.count(), 0) # Ajustado para 0


# --- CLASSE DE TESTE COMENTADA PARA FOCAR NOS BÁSICOS PRIMEIRO ---

class CSVImportTests(APITestCase):
    """Testes específicos para o endpoint de importação de CSV."""

    def setUp(self):
        # Cria usuários com emails únicos
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
        
        # Cria um CSV de teste em memória
        self.csv_content = (
            "protocol,so_number,type,status,recipient_name,cpf,provider,priority,description\n"
            "PROT-100,OS-100,administrative,open,CSV 1,111.111.111-11,technical,low,Desc 1\n"
            "PROT-101,OS-101,installation,in_progress,CSV 2,222.222.222-22,specialized,high,Desc 2\n"
        )
        self.csv_file = io.StringIO(self.csv_content)
        self.csv_file.name = "test.csv"

    def test_csv_import_admin_success(self):
        """Testa se o Admin consegue importar um CSV com sucesso."""
        self.client.force_authenticate(user=self.admin)
      
        # Reseta o ponteiro do arquivo
        self.csv_file.seek(0)
        
        response = self.client.post(
            self.import_url, 
            {'file': self.csv_file}, 
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], "Importado com sucesso 2 ordens de serviço.")
        self.assertEqual(OrdemServico.objects.count(), 2)
        # Verifica se o 'criado_por' foi o admin
        self.assertEqual(OrdemServico.objects.first().created_by, self.admin)

    def test_csv_import_regular_user_forbidden(self):
        """Testa se um usuário comum (não-staff) recebe 403 Forbidden."""
        self.client.force_authenticate(user=self.user)
        
        self.csv_file.seek(0)
        
        response = self.client.post(
            self.import_url, 
            {'file': self.csv_file}, 
            format='multipart'
        )
        
        # Graças ao [permissions.IsAdminUser], esperamos 403
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(OrdemServico.objects.count(), 0)

    def test_csv_import_invalid_data(self):
        """Testa a importação com dados inválidos (ex: prioridade errada)."""
        self.client.force_authenticate(user=self.admin)
        
        invalid_csv_content = (
            "protocol,so_number,type,status,recipient_name,cpf,provider,priority,description\n"
            "PROT-100,OS-100,admin,open,CSV 1,111.111.111-11,tech,prioridade_invalida,Desc 1\n"
        )
        invalid_file = io.StringIO(invalid_csv_content)
        invalid_file.name = "invalid.csv"
        
        response = self.client.post(
            self.import_url,
            {'file': invalid_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('details', response.data)
        # Verifica se o erro específico da 'priority' foi reportado
        self.assertIn('priority', response.data['details'][0])

