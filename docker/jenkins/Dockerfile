FROM jenkins/jenkins:lts-jdk17

USER root

# INSTALAMOS TODO LO NECESARIO: Python + Firefox + Selenium + Xvfb
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    firefox-esr \
    xvfb \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Enlazamos python3 → python (por compatibilidad)
RUN ln -s /usr/bin/python3 /usr/bin/python

# Instalamos geckodriver 0.34.0 (versión fija, evita problemas con API de GitHub)
RUN wget -O /tmp/geckodriver.tar.gz \
    https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz \
    && tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin \
    && chmod +x /usr/local/bin/geckodriver \
    && rm /tmp/geckodriver.tar.gz \
    && geckodriver --version

# LA LÍNEA MÁGICA QUE LO ARREGLA TODO CON PERFILES + CERTIFICADOS EN DOCKER
ENV MOZ_FORCE_DISABLE_E10S=1

# FORZAR PREFS COMPATIBLES PARA PERFILES
RUN mkdir -p /usr/lib/firefox/browser/defaults/preferences && \
    echo 'pref("browser.tabs.remote.autostart", false);' > /usr/lib/firefox/browser/defaults/preferences/all-jenkins.js && \
    echo 'pref("browser.tabs.remote.autostart.2", false);' >> /usr/lib/firefox/browser/defaults/preferences/all-jenkins.js && \
    echo 'pref("security.sandbox.content.level", 0);' >> /usr/lib/firefox/browser/defaults/preferences/all-jenkins.js

# Wrapper para Xvfb (opcional)
RUN echo '#!/bin/bash\nxvfb-run -a -s "-screen 0 1920x1080x24 -ac +extension RANDR" "$@"' > /usr/local/bin/run-headless \
    && chmod +x /usr/local/bin/run-headless

USER jenkins