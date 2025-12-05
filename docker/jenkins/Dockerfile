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

# Instalamos geckodriver (última versión)
RUN GECKO_LATEST=$(wget -qO- https://api.github.com/repos/mozilla/geckodriver/releases/latest \
    | grep tag_name | cut -d '"' -f 4 | cut -c2-) \
    && wget -O /tmp/geckodriver.tar.gz \
        https://github.com/mozilla/geckodriver/releases/download/v${GECKO_LATEST}/geckodriver-v${GECKO_LATEST}-linux64.tar.gz \
    && tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin \
    && chmod +x /usr/local/bin/geckodriver \
    && rm /tmp/geckodriver.tar.gz

# Wrapper para ejecutar comandos con Xvfb automáticamente
RUN echo '#!/bin/bash\nxvfb-run -a -s "-screen 0 1920x1080x24 -ac +extension RANDR" "$@"' > /usr/local/bin/run-headless \
    && chmod +x /usr/local/bin/run-headless

USER jenkins
