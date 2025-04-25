# Madryn Empleos Automatización

Este proyecto automatiza la creación de ofertas de empleo en Puerto Madryn, Argentina, utilizando SerpApi y un backend Spring Boot.

## Estructura del proyecto
- `src/`: Contiene el código principal (`scraper.py`).
- `config/`: Contiene las variables de entorno (`.env`).
- `logs/`: Almacena los logs generados por el script (opcional).
- `requirements.txt`: Dependencias del proyecto.

## Instalación
1. Clona el repositorio.
2. Crea un entorno virtual: `python -m venv venv`.
3. Activa el entorno: `venv\Scripts\activate` (Windows) o `source venv/bin/activate` (Linux/Mac).
4. Instala las dependencias: `pip install -r requirements.txt`.
5. Configura las variables de entorno en `config/.env`.

## Ejecución
- Para ejecutar normalmente: `python src/scraper.py`.
- Para probar sin restricciones de horario: `python src/scraper.py --test`.

## Deploy en Render
- Crea un Web Service en Render.
- Configura las variables de entorno (`SERPAPI_KEY`, `SPRING_BOOT_API`).
- Usa el comando de inicio: `python src/scraper.py`.