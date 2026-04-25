import mercadopago
import hashlib
import hmac
from core.config import get_settings

settings = get_settings()

sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)


def gerar_pix(sorteio_id: str, descricao: str, valor: float, email_pagador: str) -> dict:
    """
    Gera um QR Code Pix dinâmico via Mercado Pago.
    Retorna o qr_code e qr_code_base64 (imagem) para exibir no frontend.
    """
    payment_data = {
        "transaction_amount": round(valor, 2),
        "description": descricao,
        "payment_method_id": "pix",
        "payer": {
            "email": email_pagador,
        },
        "external_reference": sorteio_id,  # ID para rastrear no webhook
        "notification_url": f"{settings.MP_WEBHOOK_URL}/api/payment/webhook",
    }

    response = sdk.payment().create(payment_data)
    result = response["response"]

    if result.get("status") not in ("pending", "approved"):
        raise ValueError(f"Erro ao criar pagamento MP: {result}")

    pix_data = result["point_of_interaction"]["transaction_data"]

    return {
        "payment_id": result["id"],
        "status": result["status"],
        "qr_code": pix_data["qr_code"],
        "qr_code_base64": pix_data["qr_code_base64"],
        "valor": valor,
        "external_reference": sorteio_id,
    }


def validar_webhook_assinatura(payload: bytes, x_signature: str, x_request_id: str) -> bool:
    """
    Valida a assinatura criptografada do Webhook do Mercado Pago.
    IMPEDE que qualquer um forja um 'pagamento aprovado' falso.
    """
    try:
        parts = dict(part.split("=", 1) for part in x_signature.split(","))
        ts = parts.get("ts", "")
        v1 = parts.get("v1", "")

        signed_template = f"id:{x_request_id};request-id:{x_request_id};ts:{ts};"
        expected = hmac.new(
            settings.MP_WEBHOOK_SECRET.encode(),
            signed_template.encode(),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, v1)
    except Exception:
        return False


def buscar_status_pagamento(payment_id: int) -> str:
    """Consulta o status atual de um pagamento no Mercado Pago."""
    response = sdk.payment().get(payment_id)
    return response["response"].get("status", "unknown")
