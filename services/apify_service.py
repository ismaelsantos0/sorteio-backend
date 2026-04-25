from core.config import get_settings
import httpx

settings = get_settings()

APIFY_BASE_URL = "https://api.apify.com/v2"
ACTOR_ID = "apify~instagram-scraper"

# Custo por 1000 comentários em USD, convertido para BRL
CUSTO_POR_1000_APIFY_USD = 2.30
COTACAO_DOLAR = 5.10  # Atualizar periodicamente


def calcular_preco(contagem: int) -> float:
    """
    Calcula o preço com base na tabela de faixas definida nas variáveis de ambiente.
    Não existe tier gratuito — todo sorteio é pago.
    Retorna o valor em R$ ou -1 se ultrapassar o limite máximo (Plano PRO).
    """
    s = settings
    if contagem <= s.PRECO_LIMITE_1:
        return s.PRECO_TIER_1
    elif contagem <= s.PRECO_LIMITE_2:
        return s.PRECO_TIER_2
    elif contagem <= s.PRECO_LIMITE_3:
        return s.PRECO_TIER_3
    elif contagem <= s.PRECO_LIMITE_4:
        return s.PRECO_TIER_4
    else:
        return -1  # Sinaliza: redirecionar para Plano PRO


async def sondar_post(url_post: str) -> dict:
    """
    Fase 1 da coleta: Busca APENAS os metadados do post (commentsCount).
    Custo mínimo — não baixa comentários ainda.
    """
    headers = {"Authorization": f"Bearer {settings.APIFY_TOKEN}"}
    payload = {
        "directUrls": [url_post],
        "resultsType": "posts",   # Apenas metadados, não comentários
        "resultsLimit": 1,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        # Inicia o Actor do Apify
        resp = await client.post(
            f"{APIFY_BASE_URL}/acts/{ACTOR_ID}/runs",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        run_id = resp.json()["data"]["id"]

        # Aguarda conclusão
        run_resp = await client.get(
            f"{APIFY_BASE_URL}/actor-runs/{run_id}?waitForFinish=60",
            headers=headers,
        )
        run_resp.raise_for_status()

        # Busca os resultados
        dataset_id = run_resp.json()["data"]["defaultDatasetId"]
        items_resp = await client.get(
            f"{APIFY_BASE_URL}/datasets/{dataset_id}/items",
            headers=headers,
        )
        items_resp.raise_for_status()
        items = items_resp.json()

    if not items:
        raise ValueError("Post não encontrado ou perfil privado.")

    post = items[0]
    contagem = post.get("commentsCount", 0)
    preco = calcular_preco(contagem)

    return {
        "url": url_post,
        "shortCode": post.get("shortCode"),
        "ownerUsername": post.get("ownerUsername"),
        "commentsCount": contagem,
        "displayUrl": post.get("displayUrl"),
        "preco": preco,
        "plano_necessario": preco == -1,
    }


async def raspar_comentarios(url_post: str) -> list[dict]:
    """
    Fase 2 da coleta: Raspa TODOS os comentários (só executa após pagamento confirmado).
    """
    headers = {"Authorization": f"Bearer {settings.APIFY_TOKEN}"}
    payload = {
        "directUrls": [url_post],
        "resultsType": "comments",
        "resultsLimit": 50000,  # Máximo permitido pela tabela (até 5000 comentários)
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{APIFY_BASE_URL}/acts/{ACTOR_ID}/runs",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        run_id = resp.json()["data"]["id"]

        run_resp = await client.get(
            f"{APIFY_BASE_URL}/actor-runs/{run_id}?waitForFinish=120",
            headers=headers,
        )
        run_resp.raise_for_status()

        dataset_id = run_resp.json()["data"]["defaultDatasetId"]
        items_resp = await client.get(
            f"{APIFY_BASE_URL}/datasets/{dataset_id}/items",
            headers=headers,
        )
        items_resp.raise_for_status()
        return items_resp.json()
