#!/bin/bash
set -euo pipefail

PROFILE_DIR="/home/seluser/firefox-profile"
CERT_NAME="${CERT_NAME:-certe.p12}"   # Nombre del archivo dentro del contenedor
CERT_FILE="/home/seluser/${CERT_NAME}"
CERT_PASS="${CERT_PASS:-""}"

echo "[INFO] Perfil Firefox: $PROFILE_DIR"
mkdir -p "$PROFILE_DIR"

# Inicializar base de datos NSS si no existe
if [ ! -f "$PROFILE_DIR/cert9.db" ]; then
    echo "[INFO] Inicializando base de datos NSS..."
    certutil -N -d sql:$PROFILE_DIR --empty-password <<< ""
fi

# Importar certificado si existe
if [ -f "$CERT_FILE" ]; then
    if [ -z "$CERT_PASS" ]; then
        echo "[ERROR] CERT_PASS no definido. Aborta."
        exit 1
    fi

    echo "[INFO] Importando certificado PKCS12: $CERT_FILE"
    pk12util -i "$CERT_FILE" -d sql:$PROFILE_DIR -W "$CERT_PASS" || {
        echo "[ERROR] Fallo al importar el certificado."
        exit 1
    }

    # Obtener Key ID de la clave privada
    KEY_ID=$(certutil -K -d sql:$PROFILE_DIR | grep -v "certutil" | awk '{print $2}' | head -n 1)

    if [ -z "$KEY_ID" ]; then
        echo "[ERROR] No se encontró clave privada en el certificado."
        exit 1
    fi

    # Buscar el nickname exacto en la lista de certificados
    NICKNAME=$(certutil -L -d sql:$PROFILE_DIR | grep -B1 "$KEY_ID" | head -n 1 | sed 's/[[:space:]]*$//')

    if [ -n "$NICKNAME" ]; then
        echo "[INFO] Ajustando trust del certificado personal: $NICKNAME"
        certutil -M -n "$NICKNAME" -t "u,u,u" -d sql:$PROFILE_DIR
    else
        echo "[ERROR] No se encontró alias de certificado que coincida con la clave privada."
        certutil -L -d sql:$PROFILE_DIR
        exit 1
    fi
else
    echo "[ERROR] No existe certificado en $CERT_FILE"
    exit 1
fi

# Crear prefs.js si no existe
if [ ! -f "$PROFILE_DIR/prefs.js" ]; then
    echo "[INFO] Creando prefs.js inicial..."
    touch "$PROFILE_DIR/prefs.js"
fi

# Preferencias obligatorias
echo 'user_pref("security.default_personal_cert", "Ask Every Time");' >> "$PROFILE_DIR/prefs.js"
echo 'user_pref("security.enterprise_roots.enabled", true);' >> "$PROFILE_DIR/prefs.js"

# Validar que el certificado está en la base de datos
if ! certutil -L -d sql:$PROFILE_DIR | grep -q "$NICKNAME"; then
    echo "[ERROR] El certificado no está disponible en el perfil."
    exit 1
fi

echo "[INFO] Certificado importado y listo."
exec python3 /home/seluser/procesar_alerta.py
