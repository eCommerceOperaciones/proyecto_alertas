# Etapa 1: Extraer geckodriver desde imagen oficial de Selenium
FROM selenium/standalone-firefox:latest AS selenium_base

# Etapa 2: Imagen final con Python, Firefox y geckodriver
FROM python:3.11-slim

USER root
ENV DEBIAN_FRONTEND=noninteractive
ENV MOZ_HEADLESS=1

# Instalar Firefox y dependencias mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    firefox-esr \
    dbus \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copiar geckodriver desde la imagen Selenium
COPY --from=selenium_base /usr/bin/geckodriver /usr/local/bin/geckodriver

# Dar permisos de ejecución
RUN chmod +x /usr/local/bin/geckodriver

# Copiar dependencias Python
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ /app/src

# Crear carpeta de caché para Selenium con permisos
RUN mkdir -p /.cache/selenium && chmod -R 777 /.cache

CMD ["python", "src/main.py"]
