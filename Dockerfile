# ─────────────────────────────────────────────────────────────
# Imagen Jenkins + Firefox ESR + GeckoDriver + Xvfb
# Todo listo para Selenium sin dolores de cabeza
# ─────────────────────────────────────────────────────────────
FROM jenkins/jenkins:lts-jdk17

# Cambiar a root para instalar paquetes
USER root

# 1. Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    firefox-esr \
    xvfb \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalar GeckoDriver (versión compatible con Firefox ESR actual)
RUN FIREFOX_VERSION=$(firefox-esr --version | grep -oE '[0-9]+\.[0-9]+' | head -1) \
    && GECKO_VERSION=$(wget -qO- "https://api.github.com/repos/mozilla/geckodriver/releases/latest" \
    | grep tag_name | cut -d '"' -f 4 | sed 's/v//') \
    && wget -O /tmp/geckodriver.tar.gz \
    https://github.com/mozilla/geckodriver/releases/download/v${GECKO_VERSION}/geckodriver-v${GECKO_VERSION}-linux64.tar.gz \
    && tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin \
    && chmod +x /usr/local/bin/geckodriver \
    && rm /tmp/geckodriver.tar.gz \
    && echo "Firefox ESR $FIREFOX_VERSION + geckodriver $GECKO_VERSION instalado"

# 3. Crear script wrapper para ejecutar comandos con Xvfb automáticamente
RUN echo '#!/bin/bash\nxvfb-run -a -s "-screen 0 1920x1080x24 -ac" "$@"' > /usr/local/bin/xvfb-wrapper \
    && chmod +x /usr/local/bin/xvfb-wrapper

# 4. Volver al usuario jenkins
USER jenkins

# 5. (Opcional) Preinstalar plugins comunes
# COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
# RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# Listo
EXPOSE 8080 50000
VOLUME /var/jenkins_home