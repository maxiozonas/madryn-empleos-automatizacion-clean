import requests
from typing import List, Dict, Tuple, Optional
from src.config.settings import SERPAPI_KEY, MAX_PAGES
import time as time_module
from src.utils.logging import setup_logging

logger = setup_logging()

def scrape_google_jobs(next_page_token: Optional[str] = None, date_filter: Optional[str] = None, max_retries: int = 3, retry_delay: int = 5, query_variant: int = 0) -> Tuple[List[Dict], Optional[str], int]:
    """Obtiene empleos de SerpApi, priorizando los más recientes.
    
    Args:
        next_page_token: Token para paginación de resultados
        date_filter: Filtro de fecha (yesterday, 3days, week)
        max_retries: Número máximo de reintentos
        retry_delay: Tiempo de espera entre reintentos
        query_variant: Índice de la variante de consulta a usar (0-2)
        
    Returns:
        Tuple con: lista de empleos, token para siguiente página, y variante de consulta usada
    """
    # Consulta base - Usar variantes para capturar más resultados
    base_queries = [
        "empleos puerto madryn",
        "trabajo puerto madryn",
        "ofertas laborales puerto madryn"
    ]
    
    # Asegurarse de que el índice de variante sea válido
    if query_variant >= len(base_queries):
        query_variant = 0
        
    base_query = base_queries[query_variant]
    
    # Modificar la consulta según el filtro de fecha
    if date_filter == "date_posted:yesterday":
        query = f"{base_query} desde ayer"
        filter_desc = f"desde ayer (variante {query_variant+1}/{len(base_queries)})"
    elif date_filter == "date_posted:3days":
        query = f"{base_query} en los últimos 3 días"
        filter_desc = f"en los últimos 3 días (variante {query_variant+1}/{len(base_queries)})"
    elif date_filter == "date_posted:week":
        query = f"{base_query} en la última semana"
        filter_desc = f"en la última semana (variante {query_variant+1}/{len(base_queries)})"
    else:
        query = base_query
        filter_desc = f"sin filtro de fecha (variante {query_variant+1}/{len(base_queries)})"
    
    base_params = {
        "engine": "google_jobs",
        "q": query,
        "location": "Puerto Madryn, Chubut",
        "hl": "es",
        "gl": "ar",
        "api_key": SERPAPI_KEY,
        "sort_by": "date"  # Ordenar por fecha (más reciente primero)
    }

    jobs = []
    next_token = None
    page_count = 0
    
    # Si hay un token de página, usarlo
    if next_page_token:
        base_params["next_page_token"] = next_page_token
        
    # Intentar obtener resultados
    while page_count < MAX_PAGES:
        for attempt in range(max_retries):
            try:
                response = requests.get("https://serpapi.com/search", params=base_params, timeout=10)
                response.raise_for_status()
                data = response.json()
                jobs = data.get("jobs_results", [])
                next_token = data.get("serpapi_pagination", {}).get("next_page_token")
                
                if jobs:
                    logger.info(f"[SERPAPI] Consulta '{filter_desc}': {len(jobs)} empleos encontrados (página {page_count})")
                    return jobs, next_token, query_variant
                    
                logger.info(f"[SERPAPI] No se encontraron empleos para '{filter_desc}' (página {page_count})")
                break
            except requests.exceptions.HTTPError as e:
                logger.error(f"[SERPAPI] Error HTTP en consulta '{filter_desc}' (pág. {page_count}): {e}. Intento {attempt + 1}/{max_retries}")
                if response.status_code == 400:
                    try:
                        error_message = response.json().get("error", "No se proporcionó mensaje de error")
                        logger.error(f"Detalles del error 400: {error_message}")
                    except ValueError:
                        logger.error("No se pudo obtener el mensaje de error (respuesta no es JSON).")
                if attempt < max_retries - 1:
                    time_module.sleep(retry_delay)
            except requests.exceptions.RequestException as e:
                logger.error(f"[SERPAPI] Error de red en consulta '{filter_desc}' (pág. {page_count}): {e}. Intento {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time_module.sleep(retry_delay)

        page_count += 1
        if not next_token:
            logger.info(f"[SERPAPI] No hay más páginas de resultados para '{filter_desc}'")
            
            # Si no hay más páginas y no encontramos empleos, probar con otra variante de consulta
            next_query_variant = (query_variant + 1) % len(base_queries)
            if next_query_variant != query_variant:  # Si hay más variantes por probar
                logger.info(f"[SERPAPI] Probando con variante de consulta alternativa: {base_queries[next_query_variant]}")
                return [], None, next_query_variant
            break
            
        base_params["next_page_token"] = next_token

    # No se encontraron empleos
    logger.error(f"[SERPAPI] No se pudieron obtener empleos después de {page_count} páginas")
    return [], None, query_variant