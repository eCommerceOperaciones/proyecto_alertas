pipeline {
  agent any

  parameters {
      string(name: 'SCRIPT_NAME', defaultValue: 'acces_frontal_emd', description: 'Nombre del script a ejecutar')
      string(name: 'ALERT_NAME', defaultValue: '', description: 'Nombre de la alerta detectada')
      string(name: 'EMAIL_FROM', defaultValue: '', description: 'Remitente del correo')
      string(name: 'EMAIL_SUBJECT', defaultValue: '', description: 'Asunto del correo')
      text(name: 'EMAIL_BODY', defaultValue: '', description: 'Cuerpo del correo')
  }

  stages {
      stage('Preparar entorno') {
          steps {
              sh """
                  set -e
                  python3 -m venv venv
                  ./venv/bin/pip install --upgrade pip
                  ./venv/bin/pip install -r requirements.txt
                  mkdir -p $WORKSPACE/bin
                  if [ ! -f $WORKSPACE/bin/geckodriver ]; then
                      echo "⚙️ Instalando geckodriver..."
                      # Aquí iría la instalación si no está presente
                  else
                      echo "✅ geckodriver ya está instalado en $WORKSPACE/bin/geckodriver"
                  fi
              """
          }
      }

      stage('Mostrar datos recibidos') {
          steps {
              echo "🔔 ALERTA: ${params.ALERT_NAME}"
              echo "📧 Desde: ${params.EMAIL_FROM}"
              echo "📄 Asunto: ${params.EMAIL_SUBJECT}"
              echo "📝 Cuerpo: ${params.EMAIL_BODY}"
          }
      }

      stage('Ejecutar dispatcher / script') {
          steps {
              sh """
                  ./venv/bin/python src/runner.py \
                      --script "${params.SCRIPT_NAME}" \
                      --profile "$WORKSPACE/profiles/selenium_cert" \
                      --alert-name "${params.ALERT_NAME}" \
                      --from-email "${params.EMAIL_FROM}" \
                      --subject "${params.EMAIL_SUBJECT}" \
                      --body "${params.EMAIL_BODY}"
              """
          }
      }
  }

  post {
      always {
          echo "✅ Pipeline finalizado."
          archiveArtifacts artifacts: '**/status.txt', allowEmptyArchive: true
          emailext(
              subject: "Resultado del Job ${env.JOB_NAME}",
              body: "El job ha finalizado. Revisa el archivo status.txt para más detalles.",
              to: "ecommerceoperaciones01@gmail.com"
          )
      }
  }
}
