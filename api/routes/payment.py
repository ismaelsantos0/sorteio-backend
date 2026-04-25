import uuid
from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from services.payment_service import gerar_pix, validar_webhook_assinatura, buscar_status_pagamento
from services.apify_service import sondar_post
from core.config import get_settings

router = APIRouter(prefix="/api/payment", tags=["Pagamento"])
limiter = Limiter(key_func=get_remote_address)

# Armazenamento temporário em memória (substituir por banco de dados em produção)
# Mapeia: sorteio_id -> {url_post, status_pagamento, payment_id}
_sorteios_pendentes: dict = {}


class CheckoutRequest(BaseModel):
    url_post: str
    email: str  # Email do pagador para o Mercado Pago


@router.post("/checkout")
@limiter.limit("3/hour")  # Máximo 3 tentativas de pagamento por IP por hora
async def criar_checkout(request: Request, body: CheckoutRequest):
    """
    Gera o QR Code Pix para o sorteio.
    O preço é calculado automaticamente pela sondagem do post.
    """
    try:
        sondagem = await sondar_post(body.url_post)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro na sondagem: {str(e)}")

    if sondagem["plano_necessario"]:
        raise HTTPException(
            status_code=402,
            detail={
                "mensagem": "Post com mais de 5.000 comentários requer o Plano PRO.",
                "comentarios": sondagem["commentsCount"],
                "upgrade_url": "/plano-pro",
            }
        )

    if sondagem["preco"] == 0.0:
        raise HTTPException(status_code=400, detail="Posts grátis não precisam de checkout.")

    sorteio_id = str(uuid.uuid4())
    descricao = f"Sorteio Instagram — @{sondagem['ownerUsername']} ({sondagem['commentsCount']} comentários)"

    try:
        pix = gerar_pix(sorteio_id, descricao, sondagem["preco"], body.email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar Pix: {str(e)}")

    # Salva o estado pendente (em produção, salvar no banco de dados)
    _sorteios_pendentes[sorteio_id] = {
        "url_post": body.url_post,
        "status": "pending",
        "payment_id": pix["payment_id"],
    }

    return {
        "sorteio_id": sorteio_id,
        "qr_code": pix["qr_code"],
        "qr_code_base64": pix["qr_code_base64"],
        "valor": pix["valor"],
        "post_info": sondagem,
    }


@router.post("/webhook")
async def webhook_mercado_pago(
    request: Request,
    x_signature: str = Header(None),
    x_request_id: str = Header(None),
):
    """
    Endpoint secreto que o Mercado Pago chama quando um Pix é aprovado.
    Valida a assinatura criptográfica antes de liberar qualquer sorteio.
    """
    body_raw = await request.body()

    # --- SEGURANÇA: Validar assinatura do MP ---
    if not validar_webhook_assinatura(body_raw, x_signature or "", x_request_id or ""):
        raise HTTPException(status_code=401, detail="Assinatura do webhook inválida.")

    data = await request.json()
    action = data.get("action")
    payment_id = data.get("data", {}).get("id")

    if action == "payment.updated" and payment_id:
        status = buscar_status_pagamento(payment_id)

        if status == "approved":
            # Encontra o sorteio_id pelo payment_id
            for sorteio_id, info in _sorteios_pendentes.items():
                if info["payment_id"] == int(payment_id):
                    _sorteios_pendentes[sorteio_id]["status"] = "approved"
                    break

    return {"ok": True}


@router.get("/status/{sorteio_id}")
async def status_pagamento(sorteio_id: str):
    """
    O frontend consulta este endpoint em polling para saber se o Pix foi pago.
    """
    sorteio = _sorteios_pendentes.get(sorteio_id)
    if not sorteio:
        raise HTTPException(status_code=404, detail="Sorteio não encontrado.")

    return {"sorteio_id": sorteio_id, "status": sorteio["status"]}


@router.post("/test/approve/{sorteio_id}")
async def aprovar_pagamento_teste(sorteio_id: str):
    """
    ⚠️ APENAS EM SANDBOX — Simula a aprovação de um pagamento sem passar pelo MP.
    Bloqueado automaticamente em produção (APP_ENV=production).
    """
    if get_settings().APP_ENV == "production":
        raise HTTPException(status_code=403, detail="Endpoint disponível apenas em modo de teste.")

    sorteio = _sorteios_pendentes.get(sorteio_id)
    if not sorteio:
        raise HTTPException(status_code=404, detail="Sorteio não encontrado.")

    _sorteios_pendentes[sorteio_id]["status"] = "approved"
    return {"sorteio_id": sorteio_id, "status": "approved", "msg": "Pagamento aprovado manualmente (sandbox)."}

