from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from core.config import get_settings
from api.routes import scrape, payment, sorteio, auth

# ============================================================
# Inicialização
# ============================================================
settings = get_settings()

app = FastAPI(
    title="InstaSorteios API",
    description="Backend do SaaS de Sorteios de Comentários do Instagram",
    version="1.0.0",
    # Em produção, desabilitar o /docs para não expor a API publicamente
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    redoc_url=None,
)

# ============================================================
# Rate Limiting (Anti-Abuso Global)
# ============================================================
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================================
# CORS — Firewall do Frontend
# Apenas o domínio do Lovable/Railway pode consumir esta API
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Signature", "X-Request-ID"],
)

# ============================================================
# Registro das Rotas
# ============================================================
app.include_router(auth.router)
app.include_router(scrape.router)
app.include_router(payment.router)
app.include_router(sorteio.router)


# ============================================================
# Health Check (Railway usa para verificar se o servidor está vivo)
# ============================================================
@app.get("/", tags=["Health"])
async def health_check():
    return {
        "status": "online",
        "app": "InstaSorteios API",
        "versao": "1.0.0",
        "ambiente": settings.APP_ENV,
    }
