import re
from rest_framework.serializers import ValidationError

def validate_cpf(value):
    cpf = re.sub(r'[^0-9]', '', str(value))

    if len(cpf) != 11:
        raise ValidationError("O CPF deve conter 11 dígitos.")

    if cpf == cpf[0] * len(cpf):
        raise ValidationError("CPF inválido.")

    cnt = 0
    for i in range(10, 1, -1):
        cnt += int(cpf[10 - i]) * i

    result = (cnt * 10) % 11
    if result == 10 or result == 11:
        result = 0

    if result != int(cpf[9]):
        raise ValidationError("CPF inválido (dígitos verificadores não conferem).")

    cnt = 0
    for i in range(11, 1, -1):
        cnt += int(cpf[11 - i]) * i

    result = (cnt * 10) % 11
    if result == 10 or result == 11:
        result = 0

    if result != int(cpf[10]):
        raise ValidationError("CPF inválido (dígitos verificadores não conferem).")

    return value
