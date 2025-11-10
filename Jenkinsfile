pipeline {
  agent any

  parameters {
      string(name: 'SCRIPT_NAME', defaultValue: 'acces_frontal_emd', description: 'Nombre del script')
      string(name: 'ALERT_NAME', defaultValue: '', description: 'Nombre de la alerta')
      string(name: 'EMAIL_FROM', defaultValue: '', description: 'Remitente del correo')
      string(name: 'EMAIL_SUBJECT', defaultValue: '', description: 'Asunto del correo')
      text(name: 'EMAIL_BODY', defaultValue: '', description: 'Cuerpo del correo')
  }

  stages {
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
      }
  }
}
