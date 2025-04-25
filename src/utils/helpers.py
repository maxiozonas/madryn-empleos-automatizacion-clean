import re
from typing import Dict, List
from src.config.categories import CATEGORIES, CATEGORY_KEYWORDS
from src.config.settings import DEFAULT_LOGO_URL

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
    """Verifica si una oferta ya existe en la base de datos."""
    new_title = job.get("title", "").strip().lower()
    new_company = job.get("company_name", "").strip().lower()

    for offer in existing_offers:
        existing_title = offer.get("titulo", "").strip().lower()
        existing_company = offer.get("empresaConsultora", "").strip().lower()
        if new_title == existing_title and new_company == existing_company:
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