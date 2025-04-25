# Madryn Empleos Automatización

Sistema automatizado para la publicación programada de ofertas de empleo en Puerto Madryn, Argentina. El proyecto utiliza SerpApi para obtener datos de empleos de Google Jobs y los publica en un backend Spring Boot.

## Descripción General

Este sistema está diseñado para funcionar como un servicio automatizado que:

1. Consulta empleos disponibles en Puerto Madryn a través de SerpApi (Google Jobs)
2. Filtra empleos duplicados comparándolos con la base de datos existente
3. Publica automáticamente un número configurable de ofertas diarias (por defecto 5)
4. Distribuye las publicaciones a lo largo de un horario configurable
5. Mantiene un estado persistente para continuar correctamente tras reinicios

## Arquitectura del Sistema

### Estructura del Proyecto

```
madryn-empleos-automatizacion-clean/
├── config/                  # Configuración y variables de entorno
│   └── .env.example         # Plantilla para variables de entorno
├── resultados_test/         # Resultados de pruebas (si se ejecutan)
├── script_state.json        # Estado persistente del script
├── src/                     # Código fuente
│   ├── config/              # Configuraciones del sistema
│   │   ├── categories.py    # Categorías de empleos
│   │   └── settings.py      # Configuraciones generales
│   ├── models/              # Modelos de datos
│   ├── scheduler/           # Lógica de programación de publicaciones
│   ├── scraper/             # Módulos para obtención de datos
│   │   ├── backend.py       # Comunicación con el backend
│   │   └── serpapi.py       # Consultas a SerpApi
│   ├── utils/               # Utilidades generales
│   └── main.py              # Punto de entrada principal
├── test/                    # Pruebas unitarias
├── requirements.txt         # Dependencias del proyecto
└── README.MD                # Este archivo
```

### Componentes Principales

- **Scraper (SerpApi)**: Consulta empleos utilizando la API de SerpApi, priorizando los más recientes.
- **Backend API**: Comunica con el backend Spring Boot para publicar ofertas.
- **Scheduler**: Gestiona la programación de publicaciones a lo largo del día.
- **Sistema de Estado**: Mantiene el estado entre reinicios mediante un archivo JSON.
- **Sistema de Logging**: Registra todas las operaciones para facilitar el seguimiento.

## Configuración

### Variables de Entorno

Crea un archivo `config/.env` basado en `.env.example` con las siguientes variables:

| Variable | Descripción | Ejemplo |
|----------|-------------|--------|
| `SERPAPI_KEY` | Clave API para SerpApi | `your_serpapi_key_here` |
| `SPRING_BOOT_API` | URL base de la API backend | `your_spring_boot_api_here` |
| `USER_ID` | ID del usuario para publicaciones | `your_user_id_here` |
| `EMAIL_DEFAULT` | Email por defecto | `your_email_here` |
| `START_HOUR` | Hora de inicio para publicaciones (24h) | `9` |
| `START_MINUTE` | Minuto de inicio para publicaciones | `0` |
| `END_HOUR` | Hora de finalización para publicaciones (24h) | `18` |
| `END_MINUTE` | Minuto de finalización para publicaciones | `0` |

### Parámetros Configurables (settings.py)

- `DESIRED_OFFERS_PER_DAY`: Número de ofertas a publicar por día (por defecto: 5)
- `MAX_PAGES`: Máximo número de páginas a consultar en SerpApi
- `CHECK_INTERVAL_SECONDS`: Intervalo entre verificaciones (por defecto: 60 segundos)

## Instalación y Ejecución

### Requisitos Previos

- Python 3.9+
- Cuenta en SerpApi con créditos disponibles
- Backend Spring Boot en ejecución

### Instalación Local

1. Clona el repositorio
2. Crea un entorno virtual:
   ```bash
   python -m venv venv
   ```
3. Activa el entorno virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
5. Configura las variables de entorno en `config/.env`

### Modos de Ejecución

El script puede ejecutarse en varios modos:

1. **Modo Normal**:
   ```bash
   python src/main.py
   ```
   Ejecuta el script respetando los horarios configurados.

2. **Modo Test**:
   ```bash
   python src/main.py --test
   ```
   Publica una oferta inmediatamente, ignorando restricciones de horario.

3. **Modo Test 5 Minutos**:
   ```bash
   python src/main.py --test-5min
   ```
   Publica 5 ofertas en 5 minutos (una por minuto).

4. **Modo Test Forzado**:
   ```bash
   python src/main.py --test-force
   ```
   Fuerza la publicación inmediata de 5 ofertas.

## Despliegue en Producción

### Despliegue en Render

1. Crea un nuevo Web Service en Render
2. Conecta con el repositorio de GitHub
3. Configura el servicio:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python src/main.py`
4. Configura las variables de entorno en la sección Environment
5. Selecciona el plan adecuado (se recomienda al menos el plan Starter)

### Consideraciones para Producción

- El script incluye manejo de errores y reintentos automáticos
- Se recomienda configurar alertas en Render para monitorear el servicio
- Revisar periódicamente los logs para detectar posibles problemas

## Mantenimiento

### Logs

Los logs se generan en la consola y pueden redirigirse a un archivo. Contienen información detallada sobre:
- Consultas a SerpApi
- Ofertas encontradas y publicadas
- Errores y reintentos
- Estado del programador

### Estado Persistente

El archivo `script_state.json` mantiene el estado entre reinicios con:
- Fecha del último día de ejecución
- Número de ofertas publicadas hoy
- Última hora programada

### Solución de Problemas Comunes

- **Error de API Key**: Verificar que la clave de SerpApi sea válida y tenga créditos
- **Error de Conexión**: Comprobar la conectividad con el backend
- **No se Publican Ofertas**: Verificar los horarios configurados y los logs