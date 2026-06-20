import aiohttp
from typing import Any, Dict, Optional
import json
import base64
import logging
from pathlib import Path

from functions.database import database as db
from functions.payments._base import (
    _get_base_url,
    _sanitize_error_message,
    _post_json,
    _load_config,
    _require,
    _efi_credentials,
)

logger = logging.getLogger("eclipse_store.payments.check")

# Removido: _get_api_url, BASE_URL, _sanitize_error_message, _post_json
# Agora importados de functions.payments._base





# Mercado Pago
async def check_mp_payment(token_mp: str, payment_id: str) -> Dict[str, Any]:
    return await _post_json("check-mp-payment", {"token_mp": token_mp, "payment_id": payment_id})


# EfiBank (Efí)
async def check_efi_payment(
    client_id: str,
    client_secret: str,
    certificate: str,
    payment_id: str,
    passphrase: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "certificate": certificate,
        "payment_id": payment_id,
    }
    if passphrase is not None:
        payload["passphrase"] = passphrase
    
    result = await _post_json("check-efi-payment", payload)
    
    # Converter camelCase para snake_case para compatibilidade
    if result:
        converted = {}
        
        # Campos diretos
        if "paymentId" in result:
            converted["payment_id"] = result["paymentId"]
            converted["txid"] = result["paymentId"]  # Efi usa txid
        if "status" in result:
            converted["status"] = result["status"]
        if "statusDetail" in result:
            converted["status_detail"] = result["statusDetail"]
        if "amount" in result:
            converted["amount"] = result["amount"]
        if "paidAt" in result:
            converted["paid_at"] = result["paidAt"]
        if "checkedAt" in result:
            converted["checked_at"] = result["checkedAt"]
            
        return converted if converted else result
    
    return result


# PagBank
async def check_pagbank_payment(token_pagbank: str, payment_id: str, environment: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"token_pagbank": token_pagbank, "payment_id": payment_id}
    if environment is not None:
        payload["environment"] = environment
    return await _post_json("check-pagbank-payment", payload)


# PicPay
async def check_picpay_payment(token_picpay: str, payment_id: str) -> Dict[str, Any]:
    return await _post_json("check-picpay-payment", {"token_picpay": token_picpay, "payment_id": payment_id})


# PushinPay
async def check_pushinpay_payment(token_pushinpay: str, payment_id: str) -> Dict[str, Any]:
    return await _post_json("check-pushinpay-payment", {"token_pushinpay": token_pushinpay, "payment_id": payment_id})


# Stripe
async def check_stripe_payment(token_stripe: str, payment_id: str) -> Dict[str, Any]:
    return await _post_json("check-stripe-payment", {"token_stripe": token_stripe, "payment_id": payment_id})


# PayPal
async def check_paypal_payment(
    client_id: str,
    client_secret: str,
    payment_id: str,
    environment: Optional[str] = None,
    sandbox: Optional[bool] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "payment_id": payment_id,
    }
    if environment is not None:
        payload["environment"] = environment
    if sandbox is not None:
        payload["sandbox"] = sandbox
    return await _post_json("check-paypal-payment", payload)


# Asaas
async def check_asaas_payment(token_asaas: str, payment_id: str, environment: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"token_asaas": token_asaas, "payment_id": payment_id}
    if environment is not None:
        payload["environment"] = environment
    return await _post_json("check-asaas-payment", payload)


# Coinbase Commerce
async def check_coinbase_payment(token_coinbase: str, payment_id: str) -> Dict[str, Any]:
    return await _post_json("check-coinbase-payment", {"token_coinbase": token_coinbase, "payment_id": payment_id})


# NOWPayments
async def check_nowpayments_invoice(token_nowpayments: str, payment_id: str) -> Dict[str, Any]:
    return await _post_json("check-nowpayments-invoice", {"token_nowpayments": token_nowpayments, "payment_id": payment_id})


__all__ = [
    "check_mp_payment",
    "check_efi_payment",
    "check_pagbank_payment",
    "check_picpay_payment",
    "check_pushinpay_payment",
    "check_stripe_payment",
    "check_paypal_payment",
    "check_asaas_payment",
    "check_coinbase_payment",
    "check_nowpayments_invoice",
]


def _load_config() -> dict:
    """Carrega configurações de pagamento do database"""
    return db.get_document("payment_configs") or {}


def _require(value: Optional[str], what: str) -> str:
    if not value:
        raise ValueError(f"Missing {what} in payment settings.")
    return value


def _efi_credentials() -> Dict[str, str]:
    from pathlib import Path  # Import local para garantir disponibilidade
    cfg = _load_config().get("efibank") or {}
    client_id = cfg.get("client_id") or cfg.get("client")
    client_secret = cfg.get("client_secret") or cfg.get("token")
    cert_file = cfg.get("cert_file")
    cert_b64: Optional[str] = None
    if cert_file and isinstance(cert_file, str) and cert_file.strip():
        cert_path = Path(cert_file)
        if cert_path.exists():
            try:
                data = cert_path.read_bytes()
                cert_b64 = base64.b64encode(data).decode("ascii")
            except Exception:
                cert_b64 = None
    return {
        "client_id": _require(client_id, "Efi client_id"),
        "client_secret": _require(client_secret, "Efi client_secret"),
        "certificate": _require(cert_b64, "Efi certificate (.p12)"),
    }


# Settings-backed wrappers

async def check_mp_payment_from_settings(payment_id: str) -> Dict[str, Any]:
    token = _require((_load_config().get("mercado_pago") or {}).get("access_token"), "Mercado Pago access_token")
    return await check_mp_payment(token, payment_id)


async def check_efi_payment_from_settings(payment_id: str, passphrase: Optional[str] = None) -> Dict[str, Any]:
    creds = _efi_credentials()
    return await check_efi_payment(
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        certificate=creds["certificate"],
        payment_id=payment_id,
        passphrase=passphrase,
    )


async def check_pagbank_payment_from_settings(payment_id: str, environment: Optional[str] = None) -> Dict[str, Any]:
    token = _require((_load_config().get("pagbank") or {}).get("token_pagbank"), "PagBank token")
    return await check_pagbank_payment(token, payment_id, environment=environment)


async def check_picpay_payment_from_settings(payment_id: str) -> Dict[str, Any]:
    token = _require((_load_config().get("picpay") or {}).get("token_picpay"), "PicPay token")
    return await check_picpay_payment(token, payment_id)


async def check_pushinpay_payment_from_settings(payment_id: str) -> Dict[str, Any]:
    token = _require((_load_config().get("pushinpay") or {}).get("token_pushinpay"), "PushinPay token")
    return await check_pushinpay_payment(token, payment_id)


async def check_stripe_payment_from_settings(payment_id: str) -> Dict[str, Any]:
    token = _require((_load_config().get("stripe") or {}).get("token_stripe"), "Stripe token")
    return await check_stripe_payment(token, payment_id)


async def check_paypal_payment_from_settings(payment_id: str, environment: Optional[str] = None, sandbox: Optional[bool] = None) -> Dict[str, Any]:
    cfg = _load_config().get("paypal") or {}
    client_id = _require(cfg.get("client_id"), "PayPal client_id")
    client_secret = _require(cfg.get("client_secret"), "PayPal client_secret")
    return await check_paypal_payment(client_id, client_secret, payment_id, environment=environment, sandbox=sandbox)


async def check_asaas_payment_from_settings(payment_id: str, environment: Optional[str] = None) -> Dict[str, Any]:
    token = _require((_load_config().get("asaas") or {}).get("token_asaas"), "Asaas token")
    return await check_asaas_payment(token, payment_id, environment=environment)


async def check_coinbase_payment_from_settings(payment_id: str) -> Dict[str, Any]:
    token = _require((_load_config().get("coinbase") or {}).get("token_coinbase"), "Coinbase token")
    return await check_coinbase_payment(token, payment_id)


async def check_nowpayments_invoice_from_settings(payment_id: str) -> Dict[str, Any]:
    token = _require((_load_config().get("nowpayments") or {}).get("token_nowpayments"), "NOWPayments token")
    return await check_nowpayments_invoice(token, payment_id)


__all__ += [
    "check_mp_payment_from_settings",
    "check_efi_payment_from_settings",
    "check_pagbank_payment_from_settings",
    "check_picpay_payment_from_settings",
    "check_pushinpay_payment_from_settings",
    "check_stripe_payment_from_settings",
    "check_paypal_payment_from_settings",
    "check_asaas_payment_from_settings",
    "check_coinbase_payment_from_settings",
    "check_nowpayments_invoice_from_settings",
]
