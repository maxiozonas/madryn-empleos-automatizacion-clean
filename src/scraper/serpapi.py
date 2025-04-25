import requests
from typing import List, Dict, Tuple, Optional
from src.config.settings import SERPAPI_KEY, MAX_PAGES
import time as time_module
from src.utils.logging import setup_logging

logger = setup_logging()

def scrape_google_jobs(next_page_token: Optional[str] = None, max_retries: int = 3, retry_delay: int = 5) -> Tuple[List[Dict], Optional[str]]:
    """Obtiene empleos de SerpApi, priorizando los más recientes."""
    base_params = {
        "engine": "google_jobs",
        "q": "empleos puerto madryn",
        "location": "Puerto Madryn, Chubut",
        "hl": "es",
        "gl": "ar",
        "api_key": SERPAPI_KEY,
        "sort_by": "date"  # Ordenar por fecha (más reciente primero)
    }

    # Filtros de fecha en orden de prioridad
    date_filters = ["date_posted:today", "date_posted:yesterday", "date_posted:week"]

    jobs = []
    next_token = None
    page_count = 0

    for date_filter in date_filters:
        params = base_params.copy()
        params["chips"] = date_filter
        if next_page_token:
            params["next_page_token"] = next_page_token

        while page_count < MAX_PAGES:
            for attempt in range(max_retries):
                try:
                    response = requests.get("https://serpapi.com/search", params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    jobs = data.get("jobs_results", [])
                    next_token = data.get("serpapi_pagination", {}).get("next_page_token")
                    logger.info(f"Consulta '{date_filter}' (página {page_count}, token {next_page_token}): {len(jobs)} empleos encontrados.")
                    if jobs:
                        return jobs, next_token
                    logger.info(f"No se encontraron empleos para '{date_filter}' (página {page_count}, token {next_page_token}).")
                    break
                except requests.exceptions.HTTPError as e:
                    logger.error(f"Error HTTP ('{date_filter}', página {page_count}, token {next_page_token}): {e}. Intento {attempt + 1}/{max_retries}")
                    if response.status_code == 400:
                        try:
                            error_message = response.json().get("error", "No se proporcionó mensaje de error")
                            logger.error(f"Detalles del error 400: {error_message}")
                        except ValueError:
                            logger.error("No se pudo obtener el mensaje de error (respuesta no es JSON).")
                    if attempt < max_retries - 1:
                        time_module.sleep(retry_delay)
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error de red ('{date_filter}', página {page_count}, token {next_page_token}): {e}. Intento {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time_module.sleep(retry_delay)

            page_count += 1
            if not next_token:
                logger.info(f"No hay más páginas de resultados para '{date_filter}'.")
                break
            params["next_page_token"] = next_token

        page_count = 0
        next_token = None

    # Fallback: buscar sin filtro de fecha
    logger.info("No hay empleos recientes disponibles. Buscando sin filtro de fecha.")
    params = base_params.copy()
    params.pop("chips", None)
    if next_page_token:
        params["next_page_token"] = next_page_token

    while page_count < MAX_PAGES:
        for attempt in range(max_retries):
            try:
                response = requests.get("https://serpapi.com/search", params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                jobs = data.get("jobs_results", [])
                next_token = data.get("serpapi_pagination", {}).get("next_page_token")
                logger.info(f"Consulta sin filtro (página {page_count}, token {next_page_token}): {len(jobs)} empleos encontrados.")
                return jobs, next_token
            except requests.exceptions.HTTPError as e:
                logger.error(f"Error HTTP (sin filtro, página {page_count}, token {next_page_token}): {e}. Intento {attempt + 1}/{max_retries}")
                if response.status_code == 400:
                    try:
                        error_message = response.json().get("error", "No se proporcionó mensaje de error")
                        logger.error(f"Detalles del error 400: {error_message}")
                    except ValueError:
                        logger.error("No se pudo obtener el mensaje de error (respuesta no es JSON).")
                if attempt < max_retries - 1:
                    time_module.sleep(retry_delay)
            except requests.exceptions.RequestException as e:
                logger.error(f"Error de red (sin filtro, página {page_count}, token {next_page_token}): {e}. Intento {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time_module.sleep(retry_delay)

        page_count += 1
        if not next_token:
            logger.info("No hay más páginas de resultados sin filtro.")
            break
        params["next_page_token"] = next_token

    logger.error(f"No se pudieron obtener empleos después de {MAX_PAGES} páginas.")
    return [], None