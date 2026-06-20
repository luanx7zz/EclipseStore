import aiohttp
from typing import Any, Dict, Optional
import json
import base64
import logging
import math

from functions.database import database as db
from modules.loja.personalization.qr_customization import QRCodeGenerator
from functions.payments._base import (
    _get_base_url,
    _sanitize_error_message,
    _post_json,
    _load_config,
    _require,
    _efi_credentials,
)

logger = logging.getLogger("eclipse_store.payments.create")






# Mercado Pago
async def create_mp_payment(token_mp: str, value: float) -> Dict[str, Any]:
    # Arredondar valor para cima em 2 casas decimais
    # Exemplo: 0.5996999999999986 -> 0.60
    import math
    value = math.ceil(value * 100) / 100
    
    result = await _post_json("create-mp-payment", {"token_mp": token_mp, "value": value})
    
    # Converter camelCase para snake_case para compatibilidade
    if result:
        # Mapear campos camelCase para snake_case
        converted = {}
        
        # Campos diretos
        if "paymentId" in result:
            converted["payment_id"] = result["paymentId"]
        if "status" in result:
            converted["status"] = result["status"]
        if "amount" in result:
            converted["amount"] = result["amount"]
        if "gateway" in result:
            converted["gateway"] = result["gateway"]
        if "createdAt" in result:
            converted["created_at"] = result["createdAt"]
        if "expiresAt" in result:
            converted["expires_at"] = result["expiresAt"]
            
        # QR Code - API já retorna em base64
        if "qrCode" in result:
            converted["qr_code"] = result["qrCode"]
        if "qrCodeBase64" in result:
            converted["qr_code_base64"] = result["qrCodeBase64"]
            print(f"✅ Mercado Pago QR code recebido da API em base64")
        if "pixCopiaECola" in result:
            converted["pix_copia_cola"] = result["pixCopiaECola"]
            converted["copy_paste"] = result["pixCopiaECola"]
            
        # Se não tiver campos convertidos, retornar original
        return converted if converted else result
    
    return result


async def create_mp_site_payment(
    token_mp: str,
    value: float,
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"token_mp": token_mp, "value": value}
    if title is not None:
        payload["title"] = title
    if description is not None:
        payload["description"] = description
    return await _post_json("create-mp-site-payment", payload)


# EfiBank (Efí)
async def create_efi_payment(
    client_id: str,
    client_secret: str,
    certificate: str,
    chave_pix: str,
    price: float,
    nome_pagador: Optional[str] = None,  # Nome do usuário Discord
    passphrase: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cria pagamento Efi Bank.
    Nome: Nome do usuário Discord (se fornecido)
    CPF: Fixo 12345678909 (gerado pela API)
    """
    logger.info(f"[Efi] create_efi_payment: cert={len(certificate) if certificate else 0}b, nome={nome_pagador or 'API gerada'}")
    
    # Arredondar valor para cima em 2 casas decimais
    price = math.ceil(price * 100) / 100
    
    payload: Dict[str, Any] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "certificate": certificate,
        "chave_pix": chave_pix,
        "price": price,
    }
    
    # Adicionar nome se fornecido (API usa CPF fixo)
    if nome_pagador:
        payload["nome_pagador"] = nome_pagador
    
    if passphrase is not None:
        payload["passphrase"] = passphrase
    
    result = await _post_json("create-efi-payment", payload)
    
    # Converter camelCase para snake_case para compatibilidade
    if result:
        converted = {}
        
        # Campos diretos
        if "paymentId" in result:
            converted["payment_id"] = result["paymentId"]
            converted["txid"] = result["paymentId"]  # Efi usa txid
        if "status" in result:
            converted["status"] = result["status"]
        if "amount" in result:
            converted["amount"] = result["amount"]
        if "gateway" in result:
            converted["gateway"] = result["gateway"]
        if "createdAt" in result:
            converted["created_at"] = result["createdAt"]
        if "expiresAt" in result:
            converted["expires_at"] = result["expiresAt"]
        if "location" in result:
            converted["location"] = result["location"]
            
        # QR Code - API já retorna em base64
        if "qrCode" in result:
            converted["qr_code"] = result["qrCode"]
        if "qrCodeBase64" in result:
            converted["qr_code_base64"] = result["qrCodeBase64"]
        if "pixCopiaECola" in result:
            converted["pix_copia_cola"] = result["pixCopiaECola"]
            converted["copy_paste"] = result["pixCopiaECola"]
            
        return converted if converted else result
    
    return result


# PagBank
async def create_pagbank_payment(
    token_pagbank: str,
    value: float,
    environment: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"token_pagbank": token_pagbank, "value": value}
    if environment is not None:
        payload["environment"] = environment
    result = await _post_json("create-pagbank-payment", payload)
    
    print(f"🔍 PagBank response keys: {list(result.keys())}")
    
    # Gerar QR code se houver código PIX
    if result.get("qr_codes") and len(result["qr_codes"]) > 0:
        qr_code_data = result["qr_codes"][0]
        print(f"🔍 PagBank qr_code_data keys: {list(qr_code_data.keys())}")
        pix_code = qr_code_data.get("text") or qr_code_data.get("qrcode")
        print(f"🔍 PagBank pix_code: {pix_code[:50] if pix_code else None}...")
        if pix_code:
            try:
                qr_bytes = await QRCodeGenerator.generate_custom_qr(pix_code)
                result["qr_code_bytes"] = qr_bytes
                result["pix_copia_cola"] = pix_code
                result["copy_paste"] = pix_code
                print(f"✅ PagBank QR code gerado: {len(qr_bytes)} bytes")
            except Exception as e:
                print(f"❌ PagBank erro ao gerar QR: {e}")
    else:
        print(f"⚠️ PagBank sem qr_codes no resultado")
    
    return result


# PicPay
async def create_picpay_payment(token_picpay: str, value: float) -> Dict[str, Any]:
    return await _post_json("create-picpay-payment", {"token_picpay": token_picpay, "value": value})


# PushinPay
async def create_pushinpay_payment(
    token_pushinpay: str,
    value: int,
    webhook_url: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"token_pushinpay": token_pushinpay, "value": value}
    if webhook_url is not None:
        payload["webhook_url"] = webhook_url
    
    result = await _post_json("create-pushinpay-payment", payload)
    
    print(f"🔍 PushinPay response keys: {list(result.keys())}")
    
    # Verificar se já tem QR code em base64 da API
    if result.get("qr_code_base64") or result.get("qrcode_base64"):
        qr_base64 = result.get("qr_code_base64") or result.get("qrcode_base64")
        print(f"✅ PushinPay QR code base64 recebido da API")
        
        # Converter base64 para bytes se necessário
        try:
            import base64
            # Remover prefixo data:image/png;base64, se existir
            if "base64," in qr_base64:
                qr_base64 = qr_base64.split("base64,")[1]
            qr_bytes = base64.b64decode(qr_base64)
            result["qr_code_bytes"] = qr_bytes
            print(f"✅ PushinPay QR code convertido: {len(qr_bytes)} bytes")
        except Exception as e:
            print(f"⚠️ PushinPay erro ao converter base64: {e}")
    
    # Extrair código PIX
    pix_code = result.get("brcode") or result.get("pix_copia_cola") or result.get("qrcode") or result.get("qr_code") or result.get("copy_paste")
    
    if pix_code:
        result["pix_copia_cola"] = pix_code
        result["copy_paste"] = pix_code
        print(f"✅ PushinPay código PIX: {pix_code[:50]}...")
        
        # Se não tiver qr_code_bytes, gerar localmente
        if "qr_code_bytes" not in result:
            try:
                qr_bytes = await QRCodeGenerator.generate_custom_qr(pix_code)
                result["qr_code_bytes"] = qr_bytes
                print(f"✅ PushinPay QR code gerado localmente: {len(qr_bytes)} bytes")
            except Exception as e:
                print(f"❌ PushinPay erro ao gerar QR: {e}")
    else:
        print(f"⚠️ PushinPay sem código PIX no resultado")
    
    return result


# Stripe
async def create_stripe_payment(
    token_stripe: str,
    value: float,
    currency: str = "brl",
    success_url: str = "",
    cancel_url: str = "",
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "token_stripe": token_stripe,
        "value": value,
        "currency": currency,
        "success_url": success_url,
        "cancel_url": cancel_url,
    }
    if title is not None:
        payload["title"] = title
    if description is not None:
        payload["description"] = description
    return await _post_json("create-stripe-payment", payload)


# PayPal
async def create_paypal_payment(
    client_id: str,
    client_secret: str,
    value: float,
    currency: str = "BRL",
    return_url: str = "",
    cancel_url: str = "",
    title: Optional[str] = None,
    description: Optional[str] = None,
    environment: Optional[str] = None,
    sandbox: Optional[bool] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "value": value,
        "currency": currency,
        "return_url": return_url,
        "cancel_url": cancel_url,
    }
    if title is not None:
        payload["title"] = title
    if description is not None:
        payload["description"] = description
    if environment is not None:
        payload["environment"] = environment
    if sandbox is not None:
        payload["sandbox"] = sandbox
    return await _post_json("create-paypal-payment", payload)


# Asaas
async def create_asaas_payment_link(
    token_asaas: str,
    value: float,
    name: str = "Pagamento",
    description: Optional[str] = None,
    environment: Optional[str] = None,
    chargeType: Optional[str] = None,
    dueDateLimitDays: Optional[int] = None,
    return_url: Optional[str] = None,
    billingType: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "token_asaas": token_asaas,
        "value": value,
        "name": name,
    }
    if description is not None:
        payload["description"] = description
    if environment is not None:
        payload["environment"] = environment
    if chargeType is not None:
        payload["chargeType"] = chargeType
    if dueDateLimitDays is not None:
        payload["dueDateLimitDays"] = dueDateLimitDays
    if return_url is not None:
        payload["return_url"] = return_url
    if billingType is not None:
        payload["billingType"] = billingType
    return await _post_json("create-asaas-payment-link", payload)


async def create_asaas_pix_payment(
    token_asaas: str,
    value: float,
    customer: str,
    dueDate: Optional[str] = None,
    description: Optional[str] = None,
    environment: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "token_asaas": token_asaas,
        "value": value,
        "customer": customer,
    }
    if dueDate is not None:
        payload["dueDate"] = dueDate
    if description is not None:
        payload["description"] = description
    if environment is not None:
        payload["environment"] = environment
    return await _post_json("create-asaas-pix-payment", payload)


# Coinbase Commerce
async def create_coinbase_payment(
    token_coinbase: str,
    value: float,
    name: Optional[str] = None,
    description: Optional[str] = None,
    currency: str = "USD",
    redirect_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "token_coinbase": token_coinbase,
        "value": value,
        "currency": currency,
    }
    if name is not None:
        payload["name"] = name
    if description is not None:
        payload["description"] = description
    if redirect_url is not None:
        payload["redirect_url"] = redirect_url
    if cancel_url is not None:
        payload["cancel_url"] = cancel_url
    return await _post_json("create-coinbase-payment", payload)


# NOWPayments
async def create_nowpayments_invoice(
    token_nowpayments: str,
    value: float,
    currency: str = "USD",
    description: Optional[str] = None,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
    webhook_url: Optional[str] = None,
    order_id: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "token_nowpayments": token_nowpayments,
        "value": value,
        "currency": currency,
    }
    if description is not None:
        payload["description"] = description
    if success_url is not None:
        payload["success_url"] = success_url
    if cancel_url is not None:
        payload["cancel_url"] = cancel_url
    if webhook_url is not None:
        payload["webhook_url"] = webhook_url
    if order_id is not None:
        payload["order_id"] = order_id
    return await _post_json("create-nowpayments-invoice", payload)




# Settings-backed wrappers

# Mercado Pago
async def create_mp_payment_from_settings(value: float) -> Dict[str, Any]:
    token = _require((_load_config().get("mercado_pago") or {}).get("access_token"), "Mercado Pago access_token")
    return await create_mp_payment(token, value)


async def create_mp_site_payment_from_settings(value: float, title: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
    token = _require((_load_config().get("mercado_pago") or {}).get("access_token"), "Mercado Pago access_token")
    return await create_mp_site_payment(token, value, title=title, description=description)


# EfiBank
async def create_efi_payment_from_settings(
    price: float,
    nome_pagador: Optional[str] = None,  # Nome do usuário Discord
    chave_pix: Optional[str] = None,
    passphrase: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cria pagamento Efi Bank a partir das configurações.
    Nome: Nome do usuário Discord (se fornecido)
    CPF: Fixo 12345678909 (gerado pela API)
    """
    logger.info(f"[Efi] create_efi_payment_from_settings chamado: price={price}, nome_pagador={nome_pagador}")
    creds = _efi_credentials()
    return await create_efi_payment(
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        certificate=creds["certificate"],
        chave_pix=chave_pix or creds["pix_key"],
        price=price,
        nome_pagador=nome_pagador,
        passphrase=passphrase,
    )


# PagBank
async def create_pagbank_payment_from_settings(value: float, environment: Optional[str] = None) -> Dict[str, Any]:
    token = _require((_load_config().get("pagbank") or {}).get("token_pagbank"), "PagBank token")
    return await create_pagbank_payment(token, value, environment=environment)


# PicPay
async def create_picpay_payment_from_settings(value: float) -> Dict[str, Any]:
    token = _require((_load_config().get("picpay") or {}).get("token_picpay"), "PicPay token")
    return await create_picpay_payment(token, value)


# PushinPay
async def create_pushinpay_payment_from_settings(value: int, webhook_url: Optional[str] = None) -> Dict[str, Any]:
    token = _require((_load_config().get("pushinpay") or {}).get("token_pushinpay"), "PushinPay token")
    return await create_pushinpay_payment(token, value, webhook_url=webhook_url)


# Stripe
async def create_stripe_payment_from_settings(
    value: float,
    currency: str = "brl",
    success_url: str = "",
    cancel_url: str = "",
    title: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    token = _require((_load_config().get("stripe") or {}).get("token_stripe"), "Stripe token")
    return await create_stripe_payment(
        token, value, currency=currency, success_url=success_url, cancel_url=cancel_url, title=title, description=description
    )


# PayPal
async def create_paypal_payment_from_settings(
    value: float,
    currency: str = "BRL",
    return_url: str = "",
    cancel_url: str = "",
    title: Optional[str] = None,
    description: Optional[str] = None,
    environment: Optional[str] = None,
    sandbox: Optional[bool] = None,
) -> Dict[str, Any]:
    cfg = _load_config().get("paypal") or {}
    client_id = _require(cfg.get("client_id"), "PayPal client_id")
    client_secret = _require(cfg.get("client_secret"), "PayPal client_secret")
    return await create_paypal_payment(
        client_id,
        client_secret,
        value,
        currency=currency,
        return_url=return_url,
        cancel_url=cancel_url,
        title=title,
        description=description,
        environment=environment,
        sandbox=sandbox,
    )


# Asaas
async def create_asaas_payment_link_from_settings(
    value: float,
    name: str = "Pagamento",
    description: Optional[str] = None,
    environment: Optional[str] = None,
    chargeType: Optional[str] = None,
    dueDateLimitDays: Optional[int] = None,
    return_url: Optional[str] = None,
    billingType: Optional[str] = None,
) -> Dict[str, Any]:
    token = _require((_load_config().get("asaas") or {}).get("token_asaas"), "Asaas token")
    return await create_asaas_payment_link(
        token,
        value,
        name=name,
        description=description,
        environment=environment,
        chargeType=chargeType,
        dueDateLimitDays=dueDateLimitDays,
        return_url=return_url,
        billingType=billingType,
    )


async def create_asaas_pix_payment_from_settings(
    value: float,
    customer: str,
    dueDate: Optional[str] = None,
    description: Optional[str] = None,
    environment: Optional[str] = None,
) -> Dict[str, Any]:
    token = _require((_load_config().get("asaas") or {}).get("token_asaas"), "Asaas token")
    return await create_asaas_pix_payment(
        token,
        value,
        customer,
        dueDate=dueDate,
        description=description,
        environment=environment,
    )


# Coinbase Commerce
async def create_coinbase_payment_from_settings(
    value: float,
    name: Optional[str] = None,
    description: Optional[str] = None,
    currency: str = "USD",
    redirect_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
) -> Dict[str, Any]:
    token = _require((_load_config().get("coinbase") or {}).get("token_coinbase"), "Coinbase token")
    return await create_coinbase_payment(
        token,
        value,
        name=name,
        description=description,
        currency=currency,
        redirect_url=redirect_url,
        cancel_url=cancel_url,
    )


# NOWPayments
async def create_nowpayments_invoice_from_settings(
    value: float,
    currency: str = "USD",
    description: Optional[str] = None,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
    webhook_url: Optional[str] = None,
    order_id: Optional[str] = None,
) -> Dict[str, Any]:
    token = _require((_load_config().get("nowpayments") or {}).get("token_nowpayments"), "NOWPayments token")
    return await create_nowpayments_invoice(
        token,
        value,
        currency=currency,
        description=description,
        success_url=success_url,
        cancel_url=cancel_url,
        webhook_url=webhook_url,
        order_id=order_id,
    )


__all__ = [
    # MP
    "create_mp_payment",
    "create_mp_site_payment",
    "create_mp_payment_from_settings",
    "create_mp_site_payment_from_settings",
    # Efi
    "create_efi_payment",
    "create_efi_payment_from_settings",
    # PagBank
    "create_pagbank_payment",
    "create_pagbank_payment_from_settings",
    # PicPay
    "create_picpay_payment",
    "create_picpay_payment_from_settings",
    # PushinPay
    "create_pushinpay_payment",
    "create_pushinpay_payment_from_settings",
    # Stripe
    "create_stripe_payment",
    "create_stripe_payment_from_settings",
    # PayPal
    "create_paypal_payment",
    "create_paypal_payment_from_settings",
    # Asaas
    "create_asaas_payment_link",
    "create_asaas_pix_payment",
    "create_asaas_payment_link_from_settings",
    "create_asaas_pix_payment_from_settings",
    # Coinbase
    "create_coinbase_payment",
    "create_coinbase_payment_from_settings",
    # NOWPayments
    "create_nowpayments_invoice",
    "create_nowpayments_invoice_from_settings",
]
