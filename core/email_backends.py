import smtplib
import dns.resolver
from collections import defaultdict
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

class DirectMXEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        messages_by_domain = defaultdict(list)
        for message in email_messages:
            
            for recipient in message.recipients():
                domain = recipient.split('@')[-1]
                messages_by_domain[domain].append((message, recipient))

        sent_count = 0
        
        for domain, messages in messages_by_domain.items():
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                mx_records = sorted(mx_records, key=lambda r: r.preference)
                mx_host = str(mx_records[0].exchange)

                with smtplib.SMTP(mx_host, 25, timeout=10) as server:
                    
                    server.ehlo()
                    if server.has_extn('starttls'):
                        server.starttls()
                        server.ehlo()
                    
                    for message, recipient in messages:
                        try:
                            msg_bytes = message.message().as_bytes()
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
                if not self.fail_silently:
                    raise
                print(f"Falha ao conectar ao servidor para o domínio {domain}: {e}")
        
        return sent_count