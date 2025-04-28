import re
from typing import Dict, List
from src.config.categories import CATEGORIES, CATEGORY_KEYWORDS
from src.config.settings import DEFAULT_LOGO_URL
from src.utils.logging import setup_logging

logger = setup_logging()

def map_category(title: str, description: str) -> str:
    """Mapea una categoría basada en el título y la descripción de la oferta."""
    text = (title + " " + description).lower()

    if re.search(r"\b(ingenier[íi]a|ingeniero)\b", text) and any(keyword in text for keyword in ["software", "informática", "tecnología", "desarrollo", "programador"]):
        return CATEGORIES["Tecnología"]
    if "atención" in text and "cliente" in text:
        return CATEGORIES["Atención al Cliente"]
    if "rrhh" in text or "recursos humanos" in text:
        return CATEGORIES["Recursos Humanos"]
    if any(keyword in text for keyword in ["turismo", "guía", "patagonia", "avistaje"]):
        return CATEGORIES["Turismo"]
    if "diseñador" in text and any(keyword in text for keyword in ["gráfico", "ux", "ui", "web", "industrial"]):
        return CATEGORIES["Diseño"]
    if any(keyword in text for keyword in ["limpieza", "seguridad", "jardinero", "conserje"]) and "servicio" in text:
        return CATEGORIES["Servicios"]

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if re.search(rf"\b{keyword}\b", text):
                return CATEGORIES[category]
    return CATEGORIES["Otros"]

def get_logo_url(job: Dict) -> str:
    """Obtiene la URL del logo de la empresa, con un valor por defecto si no existe."""
    return job.get("thumbnail") or job.get("company_logo") or DEFAULT_LOGO_URL

def is_duplicate(job: Dict, existing_offers: List[Dict]) -> bool:
    """Verifica si una oferta ya existe en la base de datos.
    
    Utiliza una comparación más inteligente que permite pequeñas variaciones en los títulos
    pero mantiene el criterio estricto para la empresa para evitar falsos positivos.
    """
    new_title = job.get("title", "").strip().lower()
    new_company = job.get("company_name", "").strip().lower()
    
    # Normalizar el título (eliminar caracteres especiales y palabras comunes)
    def normalize_title(title):
        # Eliminar caracteres especiales y convertir a minúsculas
        normalized = re.sub(r'[^\w\s]', ' ', title.lower())
        # Eliminar palabras comunes que no aportan significado
        common_words = ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'de', 'del', 'para', 'por', 'en']
        words = normalized.split()
        filtered_words = [word for word in words if word not in common_words]
        return ' '.join(filtered_words)
    
    normalized_new_title = normalize_title(new_title)
    
    for offer in existing_offers:
        existing_title = offer.get("titulo", "").strip().lower()
        existing_company = offer.get("empresaConsultora", "").strip().lower()
        
        # Criterio estricto para la empresa
        if new_company != existing_company:
            continue
            
        # Para el título, usamos criterios más flexibles
        normalized_existing_title = normalize_title(existing_title)
        
        # Verificar coincidencia exacta después de normalización
        if normalized_new_title == normalized_existing_title:
            return True
            
        # Verificar si los títulos son muy similares (más del 80% de palabras coinciden)
        new_words = set(normalized_new_title.split())
        existing_words = set(normalized_existing_title.split())
        
        # Si ambos títulos tienen palabras
        if new_words and existing_words:
            # Calcular la intersección de palabras
            common_words = new_words.intersection(existing_words)
            # Calcular el porcentaje de coincidencia
            similarity = len(common_words) / max(len(new_words), len(existing_words))
            
            if similarity > 0.8:  # 80% de similitud
                return True
    
    return False

def is_blacklisted_source(job: Dict) -> bool:
    """Verifica si la oferta proviene de una fuente no deseada.
    
    Analiza de forma más precisa si la oferta proviene de las fuentes específicas
    que queremos excluir, evitando falsos positivos.
    """
    # Fuentes específicas a excluir
    blacklisted_sources = [
        "conectan2.com", 
        "bebee careers", 
        "outlier",
        "superprof"
    ]
    
    # Obtener datos relevantes
    title = job.get("title", "").lower()
    company = job.get("company_name", "").lower()
    via = job.get("via", "").lower()
    description = job.get("description", "").lower()
    extensions = job.get("extensions", [])
    detected_extensions = ', '.join(extensions).lower() if extensions else ""
    
    # Verificar la vía/fuente de la oferta (criterio más importante)
    if any(source in via for source in blacklisted_sources):
        return True
        
    # Verificar si la empresa es una de las fuentes no deseadas
    if any(source == company for source in blacklisted_sources):
        return True
    
    # Verificar patrones específicos en extensiones (más preciso que buscar en toda la descripción)
    if any(source in detected_extensions for source in blacklisted_sources):
        return True
    
    # Verificar patrones específicos en el título que indiquen fuentes no deseadas
    # (solo si el nombre exacto de la fuente aparece como palabra completa)
    for source in blacklisted_sources:
        if re.search(rf"\b{re.escape(source)}\b", title):
            return True
    
    return False

def generate_link_postulacion(job: Dict) -> str:
    """Genera un enlace de postulación basado en la plataforma."""
    via = job.get("via", "").lower()
    title = job.get("title", "").replace(" ", "+")
    company = job.get("company_name", "").replace(" ", "+")
    
    platform_urls = {
        "linkedin": f"https://www.linkedin.com/jobs/search/?keywords={title}+{company}",
        "indeed": f"https://www.indeed.com/jobs?q={title}+{company}",
        "glassdoor": f"https://www.glassdoor.com/Job/jobs.htm?suggestChosen=false&clickSource=searchBtn&typedKeyword={title}+{company}",
        "computrabajo": f"https://www.computrabajo.com.ar/ofertas-de-trabajo/?q={title}+{company}",
        "bumeran": f"https://www.bumeran.com.ar/empleos?q={title}+{company}",
        "zonajobs": f"https://www.zonajobs.com.ar/empleos?q={title}+{company}",
    }

    for platform, base_url in platform_urls.items():
        if platform in via:
            return base_url
    
    return f"https://www.google.com/search?q={title}+{company}+job"

def text_to_html(text: str) -> str:
    """Convierte texto plano a formato HTML para el editor TipTap.
    
    Procesa el texto para mantener el formato de:
    - Párrafos
    - Secciones (como 'Responsabilidades:', 'Requisitos:', 'Beneficios:')
    - Listas con viñetas (detecta líneas que comienzan con - • * o ◦)
    - Listas numeradas (detecta líneas que comienzan con números seguidos de punto o paréntesis)
    """
    if not text:
        return "<p></p>"
    
    # Normalizar saltos de línea
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Dividir en líneas
    lines = text.split('\n')
    result = []
    
    # Patrones para detectar secciones (palabras seguidas de dos puntos)
    section_pattern = r'^([A-Za-zÁÉÍÓÚáéíóúÑñ\s]+):$'
    
    i = 0
    in_list = False
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Saltar líneas vacías
        if not line:
            if in_list:
                # Cerrar la lista si estábamos en una
                result.append('</ul>')
                in_list = False
            i += 1
            continue
        
        # Detectar secciones (como "Responsabilidades:", "Requisitos:", "Beneficios:")
        section_match = re.match(section_pattern, line)
        if section_match:
            if in_list:
                # Cerrar la lista anterior si estábamos en una
                result.append('</ul>')
                in_list = False
            
            # Agregar la sección como un párrafo con estilo de encabezado
            result.append(f'<p><strong>{line}</strong></p>')
            i += 1
            continue
        
        # Detectar listas con viñetas
        if re.match(r'^[\-•\*◦]\s+', line):
            # Iniciar lista si no estamos ya en una
            if not in_list:
                result.append('<ul>')
                in_list = True
            
            # Extraer el contenido sin el marcador de viñeta
            content = re.sub(r'^[\-•\*◦]\s+', '', line)
            
            # Verificar si el contenido contiene texto en negrita (como "Responsabilidades:")
            bold_match = re.match(r'^([A-Za-zÁÉÍÓÚáéíóúÑñ\s]+):(.*)$', content)
            if bold_match:
                section_title = bold_match.group(1)
                rest_content = bold_match.group(2).strip()
                if rest_content:
                    content = f'<strong>{section_title}:</strong>{rest_content}'
                else:
                    content = f'<strong>{section_title}:</strong>'
            
            result.append(f'  <li>{content}</li>')
        
        # Detectar listas numeradas
        elif re.match(r'^\d+[\.)]\s*', line):
            # Cerrar lista de viñetas si estábamos en una
            if in_list:
                result.append('</ul>')
                in_list = False
            
            # Iniciar lista numerada
            if not (result and result[-1] == '<ol>'):
                result.append('<ol>')
            
            # Extraer el contenido sin el número
            content = re.sub(r'^\d+[\.)]\s*', '', line)
            result.append(f'  <li>{content}</li>')
            
            # Verificar si la siguiente línea también es parte de la lista numerada
            if i + 1 < len(lines) and re.match(r'^\d+[\.)]\s*', lines[i + 1].strip()):
                i += 1
                continue
            else:
                result.append('</ol>')
        
        # Párrafo normal
        else:
            if in_list:
                # Cerrar la lista si estábamos en una
                result.append('</ul>')
                in_list = False
            
            # Buscar líneas consecutivas que formen un párrafo
            paragraph = [line]
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                # Si la siguiente línea está vacía, es parte de una lista, o es una sección, terminar el párrafo
                if (not next_line or 
                    re.match(r'^[\-•\*◦]\s+', next_line) or 
                    re.match(r'^\d+[\.)]\s*', next_line) or
                    re.match(section_pattern, next_line)):
                    break
                paragraph.append(next_line)
                j += 1
            
            # Unir las líneas del párrafo y envolverlas en etiquetas <p>
            result.append(f'<p>{" ".join(paragraph)}</p>')
            i = j - 1  # Ajustar el índice para continuar desde donde terminó el párrafo
        
        i += 1
    
    # Cerrar cualquier lista abierta
    if in_list:
        result.append('</ul>')
    
    # Si el texto no generó ningún contenido HTML, crear al menos un párrafo vacío
    if not result:
        return "<p></p>"
    
    return '\n'.join(result)