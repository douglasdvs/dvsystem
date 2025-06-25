import re
from typing import Union, Tuple

def validar_cpf(cpf: str) -> bool:
    """
    Valida um CPF.
    
    Args:
        cpf: CPF a ser validado (com ou sem máscara)
        
    Returns:
        bool: True se o CPF é válido, False caso contrário
    """
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se todos os dígitos são iguais
    if len(set(cpf)) == 1:
        return False
    
    # Calcula primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10 % 11) % 10
    if int(cpf[9]) != digito1:
        return False
    
    # Calcula segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10 % 11) % 10
    if int(cpf[10]) != digito2:
        return False
    
    return True

def validar_cnpj(cnpj: str) -> bool:
    """
    Valida um CNPJ.
    
    Args:
        cnpj: CNPJ a ser validado (com ou sem máscara)
        
    Returns:
        bool: True se o CNPJ é válido, False caso contrário
    """
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais
    if len(set(cnpj)) == 1:
        return False
    
    # Calcula primeiro dígito verificador
    multiplicadores = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * multiplicadores[i] for i in range(12))
    digito1 = 11 - (soma % 11)
    if digito1 > 9:
        digito1 = 0
    if int(cnpj[12]) != digito1:
        return False
    
    # Calcula segundo dígito verificador
    multiplicadores = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * multiplicadores[i] for i in range(13))
    digito2 = 11 - (soma % 11)
    if digito2 > 9:
        digito2 = 0
    if int(cnpj[13]) != digito2:
        return False
    
    return True

def validar_cpf_cnpj(cpf_cnpj: str) -> Tuple[bool, str]:
    """
    Valida um CPF ou CNPJ.
    
    Args:
        cpf_cnpj: CPF ou CNPJ a ser validado (com ou sem máscara)
        
    Returns:
        Tuple[bool, str]: (True/False, 'CPF'/'CNPJ'/'INVALIDO')
    """
    # Remove caracteres não numéricos
    cpf_cnpj = re.sub(r'[^0-9]', '', cpf_cnpj)
    
    if len(cpf_cnpj) == 11:
        return validar_cpf(cpf_cnpj), 'CPF'
    elif len(cpf_cnpj) == 14:
        return validar_cnpj(cpf_cnpj), 'CNPJ'
    return False, 'INVALIDO'

def formatar_cpf_cnpj(cpf_cnpj: str) -> str:
    """
    Formata um CPF ou CNPJ com máscara.
    
    Args:
        cpf_cnpj: CPF ou CNPJ a ser formatado (com ou sem máscara)
        
    Returns:
        str: CPF ou CNPJ formatado
    """
    # Remove caracteres não numéricos
    cpf_cnpj = re.sub(r'[^0-9]', '', cpf_cnpj)
    
    if len(cpf_cnpj) == 11:
        return f'{cpf_cnpj[:3]}.{cpf_cnpj[3:6]}.{cpf_cnpj[6:9]}-{cpf_cnpj[9:]}'
    elif len(cpf_cnpj) == 14:
        return f'{cpf_cnpj[:2]}.{cpf_cnpj[2:5]}.{cpf_cnpj[5:8]}/{cpf_cnpj[8:12]}-{cpf_cnpj[12:]}'
    return cpf_cnpj

def validar_telefone(telefone: str) -> bool:
    """
    Valida um número de telefone.
    
    Args:
        telefone: Telefone a ser validado (com ou sem máscara)
        
    Returns:
        bool: True se o telefone é válido, False caso contrário
    """
    # Remove caracteres não numéricos
    telefone = re.sub(r'[^0-9]', '', telefone)
    
    # Verifica se tem entre 10 e 11 dígitos (com DDD)
    if len(telefone) not in [10, 11]:
        return False
    
    # Verifica se o DDD é válido (11 a 99)
    ddd = int(telefone[:2])
    if ddd < 11 or ddd > 99:
        return False
    
    return True

def formatar_telefone(telefone: str) -> str:
    """
    Formata um número de telefone com máscara.
    
    Args:
        telefone: Telefone a ser formatado (com ou sem máscara)
        
    Returns:
        str: Telefone formatado
    """
    # Remove caracteres não numéricos
    telefone = re.sub(r'[^0-9]', '', telefone)
    
    if len(telefone) == 11:
        return f'({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}'
    elif len(telefone) == 10:
        return f'({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}'
    return telefone

def validar_email(email: str) -> bool:
    """
    Valida um endereço de email.
    
    Args:
        email: Email a ser validado
        
    Returns:
        bool: True se o email é válido, False caso contrário
    """
    # Regex mais completa para validação de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False
    
    # Verifica se o domínio tem pelo menos um ponto
    if '.' not in email.split('@')[1]:
        return False
    
    # Verifica se não tem caracteres especiais no início ou fim
    if email.startswith('.') or email.endswith('.'):
        return False
    
    # Verifica se não tem espaços
    if ' ' in email:
        return False
    
    return True

def validar_cep(cep: str) -> bool:
    """
    Valida um CEP.
    
    Args:
        cep: CEP a ser validado (com ou sem máscara)
        
    Returns:
        bool: True se o CEP é válido, False caso contrário
    """
    # Remove caracteres não numéricos
    cep = re.sub(r'[^0-9]', '', cep)
    
    # Verifica se tem 8 dígitos
    if len(cep) != 8:
        return False
    
    # Verifica se todos os dígitos são iguais
    if len(set(cep)) == 1:
        return False
    
    return True

def formatar_cep(cep: str) -> str:
    """
    Formata um CEP com máscara.
    
    Args:
        cep: CEP a ser formatado (com ou sem máscara)
        
    Returns:
        str: CEP formatado
    """
    # Remove caracteres não numéricos
    cep = re.sub(r'[^0-9]', '', cep)
    
    if len(cep) == 8:
        return f'{cep[:5]}-{cep[5:]}'
    return cep 