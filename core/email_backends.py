import smtplib
import dns.resolver
from collections import defaultdict
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

class DirectMXEmailBackend(BaseEmailBackend):
    """
    Um Backend de E-mail Django que resolve o MX record
    do domínio do destinatário e envia o e-mail diretamente.
    """
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)

    def send_messages(self, email_messages):
        """
        Envia um ou mais objetos EmailMessage.
        Retorna o número de mensagens enviadas.
        """
        if not email_messages:
            return 0

        # Agrupa mensagens por domínio de destino
        # (ex: todos os e-mails para '@gmail.com' vão juntos)
        messages_by_domain = defaultdict(list)
        for message in email_messages:
            
            # --- CORREÇÃO AQUI ---
            # O método correto é .recipients(), não .get_recipients()
            for recipient in message.recipients():
            # ---------------------
                
                domain = recipient.split('@')[-1]
                messages_by_domain[domain].append((message, recipient))

        sent_count = 0
        
        for domain, messages in messages_by_domain.items():
            try:
                # 1. Resolver o MX Record
                mx_records = dns.resolver.resolve(domain, 'MX')
                # Ordena por preferência e pega o de menor número (maior prioridade)
                mx_records = sorted(mx_records, key=lambda r: r.preference)
                mx_host = str(mx_records[0].exchange)

                # 2. Conectar ao servidor de e-mail
                with smtplib.SMTP(mx_host, 25, timeout=10) as server:
                    
                    # 3. Tentar usar uma conexão segura (STARTTLS)
                    server.ehlo()
                    if server.has_extn('starttls'):
                        server.starttls()
                        server.ehlo() # Re-identifica após TLS
                    
                    # 4. Enviar os e-mails para este domínio
                    for message, recipient in messages:
                        try:
                            # Converte a mensagem do Django para bytes
                            msg_bytes = message.message().as_bytes()
                            # Envia o e-mail (para este destinatário específico)
                            server.sendmail(
                                message.from_email, 
                                [recipient], 
                                msg_bytes
                            )
                            sent_count += 1
                        except smtplib.SMTPException as e:
                            if not self.fail_silently:
                                raise
                            print(f"Falha ao enviar e-mail para {recipient}: {e}")
                            
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, smtplib.SMTPException) as e:
                # Se o DNS falhar ou o SMTP falhar para o domínio inteiro
                if not self.fail_silently:
                    raise
                print(f"Falha ao conectar ao servidor para o domínio {domain}: {e}")
        
        return sent_count