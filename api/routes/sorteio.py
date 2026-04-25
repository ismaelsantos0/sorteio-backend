from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.apify_service import raspar_comentarios
from services.sorteio_service import realizar_sorteio
from api.routes.payment import _sorteios_pendentes  # Em produção: buscar do banco

router = APIRouter(prefix="/api/sorteio", tags=["Sorteio"])


class SorteioRequest(BaseModel):
    sorteio_id: str            # ID gerado no checkout
    remover_duplicados: bool = True
    filtro_palavra: Optional[str] = None  # Ex: "@amigo", "quero"


@router.post("/executar")
async def executar_sorteio(body: SorteioRequest):
    """
    Motor 2 — Fase 2: Raspa os comentários e realiza o sorteio.
    SÓ executa se o pagamento do sorteio_id estiver 'approved'.
    """
    sorteio = _sorteios_pendentes.get(body.sorteio_id)

    if not sorteio:
        raise HTTPException(status_code=404, detail="Sorteio não encontrado.")

    # --- SEGURANÇA: Bloqueia sorteio sem pagamento confirmado ---
    if sorteio["status"] != "approved":
        raise HTTPException(
            status_code=402,
            detail="Pagamento ainda não confirmado. Aguarde a aprovação do Pix."
        )

    url_post = sorteio["url_post"]

    try:
        comentarios = await raspar_comentarios(url_post)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao raspar comentários: {str(e)}")

    try:
        resultado = realizar_sorteio(
            comentarios,
            remover_duplicados=body.remover_duplicados,
            filtro_palavra=body.filtro_palavra,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Marca o sorteio como concluído para evitar reuso
    _sorteios_pendentes[body.sorteio_id]["status"] = "completed"

    return {
        "sorteio_id": body.sorteio_id,
        **resultado,
    }
