import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    email = models.EmailField(_('email address'), unique=True, blank=False, null=False)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_user'
        swappable = 'AUTH_USER_MODEL'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']

class ServiceOrderType(models.TextChoices):
    ADMINISTRATIVE = 'administrative', _('Administrativa')
    INSTALLATION = 'installation', _('Instalação')
    PREVENTIVE_MAINTENANCE = 'preventive_maintenance', _('Manutenção Preventiva')
    CORRECTIVE_MAINTENANCE = 'corrective_maintenance', _('Manutenção Corretiva')
    PREDICTIVE_MAINTENANCE = 'predictive_maintenance', _('Manutenção Preditiva')
    INSPECTION = 'inspection', _('Vistoria')
    TECHNICAL_ASSISTANCE = 'technical_assistance', _('Assistência Técnica')
    WORK_SAFETY = 'work_safety', _('Segurança do Trabalho')
    BUDGET = 'budget', _('Orçamento')
    EVENTS = 'events', _('Eventos')

class ServiceOrderStatus(models.TextChoices):
    OPEN = 'open', _('Aberta')
    IN_PROGRESS = 'in_progress', _('Em andamento')
    COMPLETED = 'completed', _('Concluída')
    CANCELLED = 'cancelled', _('Cancelada')

class ServiceProviderType(models.TextChoices):
    TECHNICAL = 'technical', _('Técnico')
    SPECIALIZED = 'specialized', _('Especializado')
    CONSULTING = 'consulting', _('Consultivo')
    ADMINISTRATIVE = 'administrative_provider', _('Administrativo')
    LOGISTICS = 'logistics', _('Logístico')
    OPERATIONAL = 'operational', _('Operacional')
    TECHNOLOGICAL = 'technological', _('Tecnológico')
    COMMERCIAL = 'commercial', _('Comercial')
    MAINTENANCE = 'maintenance_provider', _('Manutenção')
    SECURITY = 'security', _('Segurança')
    EDUCATIONAL = 'educational', _('Educacional')
    COMMUNICATION = 'communication', _('Comunicação')
    OTHER = 'other', _('Outros Serviços')

class ServiceOrderPriority(models.TextChoices):
    CRITICAL = 'critical', _('Crítica')
    HIGH = 'high', _('Alta')
    MEDIUM = 'medium', _('Média')
    LOW = 'low', _('Baixa')


class ServiceOrder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    protocol = models.CharField(max_length=100, unique=True, db_index=True, help_text=_("Protocolo único da O.S."))
    so_number = models.CharField(max_length=100, db_index=True, verbose_name=_("Número da O.S."))
    
    type = models.CharField(
        max_length=50,
        choices=ServiceOrderType.choices,
        default=ServiceOrderType.CORRECTIVE_MAINTENANCE,
        verbose_name=_("Tipo de Serviço")
    )
    status = models.CharField(
        max_length=50,
        choices=ServiceOrderStatus.choices,
        default=ServiceOrderStatus.OPEN,
        verbose_name=_("Status")
    )
    provider = models.CharField(
        max_length=50,
        choices=ServiceProviderType.choices,
        default=ServiceProviderType.TECHNICAL,
        verbose_name=_("Prestador")
    )
    priority = models.CharField(
        max_length=50,
        choices=ServiceOrderPriority.choices,
        default=ServiceOrderPriority.MEDIUM,
        verbose_name=_("Prioridade")
    )

    recipient_name = models.CharField(max_length=255, verbose_name=_("Nome do Recebedor/Cliente"))
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name=_("CPF"))
    
    description = models.TextField(verbose_name=_("Descrição"))
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_orders',
        verbose_name=_("Criado por")
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Criado em"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Atualizado em"))

    class Meta:
        verbose_name = _("Ordem de Serviço")
        verbose_name_plural = _("Ordens de Serviço")
        ordering = ['-created_at']

    def __str__(self):
        return f"O.S. {self.so_number} ({self.get_status_display()})"
