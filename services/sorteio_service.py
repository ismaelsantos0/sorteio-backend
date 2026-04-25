import random
from typing import Optional


def realizar_sorteio(
    comentarios: list[dict],
    remover_duplicados: bool = True,
    filtro_palavra: Optional[str] = None,
) -> dict:
    """
    Algoritmo central do sorteio. Aplica os filtros e sorteia 1 vencedor.

    Args:
        comentarios: Lista de comentários brutos do Apify.
        remover_duplicados: Se True, cada usuário tem apenas 1 chance.
        filtro_palavra: Se preenchido, só valida comentários que contenham esta palavra/menção.

    Returns:
        Dicionário com o vencedor e as estatísticas do sorteio.
    """
    participantes = comentarios.copy()

    # --- Filtro 1: Palavra-chave ou menção obrigatória ---
    if filtro_palavra:
        termo = filtro_palavra.lower().strip()
        participantes = [
            c for c in participantes
            if termo in c.get("text", "").lower()
        ]

    # --- Filtro 2: Remover duplicados (1 chance por usuário) ---
    if remover_duplicados:
        vistos = set()
        unicos = []
        for c in participantes:
            username = c.get("ownerUsername", "").lower()
            if username and username not in vistos:
                vistos.add(username)
                unicos.append(c)
        participantes = unicos

    if not participantes:
        raise ValueError("Nenhum comentário válido após aplicar os filtros.")

    # --- Sorteio ---
    vencedor = random.choice(participantes)

    return {
        "vencedor": {
            "username": vencedor.get("ownerUsername"),
            "comentario": vencedor.get("text"),
            "foto_perfil": vencedor.get("ownerProfilePicUrl"),
            "id_comentario": vencedor.get("id"),
        },
        "estatisticas": {
            "total_comentarios_brutos": len(comentarios),
            "total_participantes_validos": len(participantes),
            "filtro_palavra_aplicado": filtro_palavra,
            "duplicados_removidos": remover_duplicados,
        },
    }
