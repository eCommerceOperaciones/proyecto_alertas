FROM python:3.12-slim

ENV PROFILE_DIR=/home/seluser/firefox-profile
ENV CERT_FILE=certificado.p12
ENV CERT_PASSWORD="1234"

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    libnss3-tools \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz \
    && tar -xzf geckodriver-v0.34.0-linux64.tar.gz \
    && mv geckodriver /usr/local/bin/ \
    && rm geckodriver-v0.34.0-linux64.tar.gz

RUN pip install --no-cache-dir selenium

RUN useradd -m seluser
USER seluser
WORKDIR /home/seluser

COPY ${CERT_FILE} /home/seluser/${CERT_FILE}
COPY procesar_alerta.py /home/seluser/procesar_alerta.py

# Crear perfil y base NSS sin usar Firefox
RUN mkdir -p ${PROFILE_DIR} && \
    certutil -N -d sql:${PROFILE_DIR} --empty-password && \
    pk12util -i ${CERT_FILE} -d sql:${PROFILE_DIR} -W "${CERT_PASSWORD}" && \
    echo 'user_pref("security.default_personal_cert", "Select Automatically");' >> ${PROFILE_DIR}/prefs.js

CMD ["python", "procesar_alerta.py"]