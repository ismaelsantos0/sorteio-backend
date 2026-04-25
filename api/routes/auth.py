from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from core.config import get_settings
from core.security import create_access_token

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])
settings = get_settings()

META_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"
META_ME_URL = "https://graph.facebook.com/me"


class FacebookLoginRequest(BaseModel):
    code: str          # Código de autorização recebido do Login com Facebook no Frontend
    redirect_uri: str  # URI de redirecionamento configurada no App Meta


@router.post("/login")
async def login_com_facebook(body: FacebookLoginRequest):
    """
    Troca o código de autorização do Facebook por um JWT do nosso sistema.
    O Frontend envia o 'code' recebido do OAuth do Facebook.
    """
    async with httpx.AsyncClient() as client:
        # Troca o code por um access_token do Facebook
        token_resp = await client.get(META_TOKEN_URL, params={
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "redirect_uri": body.redirect_uri,
            "code": body.code,
        })

        if token_resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Código de autorização do Facebook inválido.")

        fb_token = token_resp.json().get("access_token")

        # Busca os dados do usuário no Facebook
        me_resp = await client.get(META_ME_URL, params={
            "fields": "id,name,email,picture",
            "access_token": fb_token,
        })

        if me_resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Falha ao buscar dados do usuário no Facebook.")

        user_data = me_resp.json()

    # Gera o nosso JWT interno (não expõe o token do Facebook ao Front-end)
    jwt_token = create_access_token({
        "sub": user_data["id"],
        "name": user_data.get("name"),
        "email": user_data.get("email"),
        "fb_token": fb_token,  # Guardado para chamadas futuras à Graph API
        "plano": "free",       # Em produção: buscar do banco de dados
    })

    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "user": {
            "id": user_data["id"],
            "name": user_data.get("name"),
            "picture": user_data.get("picture", {}).get("data", {}).get("url"),
        }
    }
