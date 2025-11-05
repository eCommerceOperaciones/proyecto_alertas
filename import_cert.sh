#!/bin/bash
CERT_PATH=$1
CERT_PASSWORD=$2

if [ -z "$CERT_PATH" ] || [ -z "$CERT_PASSWORD" ]; then
  echo "Uso: import_cert.sh <ruta_certificado.p12> <contraseña>"
  exit 1
fi

echo "Importando certificado en el perfil de Firefox..."
certutil -d sql:/home/jenkins/firefox-profile -A -t "CT,C,C" -n "MiCertificado" -i "$CERT_PATH" -f <(echo "$CERT_PASSWORD")
