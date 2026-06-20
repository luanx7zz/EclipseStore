"""
Templates de mensagem reutilizáveis para o bot.
Fornece placeholders e formatação padronizada.
"""
import re
import logging
logger = logging.getLogger("eclipse_store.messages.template")

# Placeholders disponíveis
PLACEHOLDERS = {
    "{user}": "Nome do usuário",
    "{user_mention}": "Menção do usuário",
    "{user_id}": "ID do usuário",
    "{guild}": "Nome do servidor",
    "{product}": "Nome do produto",
    "{price}": "Preço",
    "{quantity}": "Quantidade",
}


def render(template: str, **kwargs) -> str:
    """
    Substitui placeholders em um template.
    
    Args:
        template: String com {placeholders}.
        **kwargs: Valores para cada placeholder.
    
    Returns:
        String com placeholders substituídos.
    """
    if not template:
        return ""
    result = template
    for key, value in kwargs.items():
        result = result.replace("{" + key + "}", str(value))
    return result


def validate_template(template: str) -> tuple[bool, str]:
    """
    Valida se um template tem placeholders válidos.
    Retorna (válido, mensagem_erro).
    """
    unknown = re.findall(r"\{(\w+)\}", template)
    valid_keys = {k.strip("{}") for k in PLACEHOLDERS}
    invalid = [u for u in unknown if u not in valid_keys]
    if invalid:
        return False, f"Placeholders desconhecidos: {', '.join(invalid)}"
    return True, ""
