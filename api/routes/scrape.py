from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, HttpUrl
from slowapi import Limiter
from slowapi.util import get_remote_address
from services.apify_service import sondar_post

router = APIRouter(prefix="/api/scrape", tags=["Scraping"])
limiter = Limiter(key_func=get_remote_address)


class SondagemRequest(BaseModel):
    url_post: str  # Ex: "https://www.instagram.com/p/XXXXXXXX/"


@router.post("/sondagem")
@limiter.limit("5/hour")  # Máximo 5 sondagens por IP por hora (anti-abuso)
async def sondar(request: Request, body: SondagemRequest):
    """
    Fase 1 do Motor 2: Sonda o post do Instagram e retorna a contagem de comentários
    e o preço a ser cobrado. NÃO raspa os comentários ainda (sem custo alto).
    """
    if "instagram.com/p/" not in body.url_post:
        raise HTTPException(status_code=400, detail="URL inválida. Use um link de post do Instagram.")

    try:
        resultado = await sondar_post(body.url_post)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao contatar o Apify: {str(e)}")

    return resultado
