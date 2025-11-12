pipeline {
  agent { label 'main' }

  parameters {
      string(name: 'SCRIPT_NAME', defaultValue: '', description: 'Nombre lógico del script registrado en dispatcher')
      string(name: 'RETRY_COUNT', defaultValue: '0', description: 'Contador de reintentos automáticos')
      string(name: 'ALERT_NAME', defaultValue: '', description: 'Nombre de la alerta detectada')
      string(name: 'ALERT_TYPE', defaultValue: '', description: 'Tipo de alerta: ACTIVA o RESUELTA')
      string(name: 'ALERT_ID', defaultValue: '', description: 'ID de la alerta en Excel (opcional)')
      string(name: 'EMAIL_FROM', defaultValue: '', description: 'Remitente del correo')
      string(name: 'EMAIL_SUBJECT', defaultValue: '', description: 'Asunto del correo')
      text(name: 'EMAIL_BODY', defaultValue: '', description: 'Contenido del correo')
      string(name: 'MAX_RETRIES', defaultValue: '1', description: 'Número máximo de reintentos permitidos')
  }

  environment {
      WORKSPACE_BIN = "${WORKSPACE}/bin"
      PYTHON_VENV = "${WORKSPACE}/venv"
      SHARED_EXCEL = "${WORKSPACE}/alertas.xlsx" // Cambiado para WSL
  }

  stages {

      stage('Validar parámetros y credenciales') {
          steps {
              script {
                  if (!params.SCRIPT_NAME || !params.ALERT_NAME) {
                      error("Parámetros críticos faltantes: SCRIPT_NAME y ALERT_NAME son obligatorios.")
                  }
              }
              withCredentials([
                  usernamePassword(credentialsId: 'email-alertas-user', usernameVariable: 'EMAIL_CREDS_USR', passwordVariable: 'EMAIL_CREDS_PSW'),
                  usernamePassword(credentialsId: 'jenkins-api', usernameVariable: 'JENKINS_CREDS_USR', passwordVariable: 'JENKINS_CREDS_PSW')
              ]) {
                  echo "✅ Credenciales cargadas correctamente."
              }
          }
      }

      stage('Checkout') {
          steps {
              git branch: 'Dev_Sondas', url: 'https://github.com/eCommerceOperaciones/proyecto_alertas.git'
          }
      }

      stage('Preparar entorno') {
          steps {
              sh """
                  python3 -m venv ${PYTHON_VENV}
                  ${PYTHON_VENV}/bin/pip install --upgrade pip
                  ${PYTHON_VENV}/bin/pip install -r requirements.txt
              """
          }
      }

      stage('Ejecutar script de alerta') {
          steps {
              sh """
                  ${PYTHON_VENV}/bin/python src/runner.py \
                      --script ${params.SCRIPT_NAME} \
                      --profile "$WORKSPACE/profiles/selenium_cert" \
                      --alert-name "${params.ALERT_NAME}" \
                      --from-email "${params.EMAIL_FROM}" \
                      --subject "${params.EMAIL_SUBJECT}" \
                      --body "${params.EMAIL_BODY}" \
                      --retry ${params.RETRY_COUNT} \
                      --max-retries ${params.MAX_RETRIES}
              """
          }
      }
      
      stage('Ejecutar script de alerta con reintento') {
  steps {
      script {
          def retries = params.RETRY_COUNT.toInteger()
          def maxRetries = params.MAX_RETRIES.toInteger()
          def statusFile = "${WORKSPACE}/status.txt"

          // Ejecutar runner.py
          sh """
              ${PYTHON_VENV}/bin/python src/runner.py \
                  --script ${params.SCRIPT_NAME} \
                  --profile "$WORKSPACE/profiles/selenium_cert" \
                  --alert-name "${params.ALERT_NAME}" \
                  --from-email "${params.EMAIL_FROM}" \
                  --subject "${params.EMAIL_SUBJECT}" \
                  --body "${params.EMAIL_BODY}" \
                  --retry ${retries} \
                  --max-retries ${maxRetries}
          """

          // Leer status.txt
          def status = readFile(statusFile).trim()
          echo "Estado devuelto por script: ${status}"

          if (status == "falso_positivo" && retries < maxRetries) {
              echo "Falso positivo detectado. Reintentando en 5 minutos..."
              sleep(time: 5, unit: "MINUTES")
              // Relanzar el mismo stage con RETRY_COUNT incrementado
              build job: env.JOB_NAME, parameters: [
                  string(name: 'SCRIPT_NAME', value: params.SCRIPT_NAME),
                  string(name: 'RETRY_COUNT', value: "${retries + 1}"),
                  string(name: 'ALERT_NAME', value: params.ALERT_NAME),
                  string(name: 'ALERT_TYPE', value: params.ALERT_TYPE),
                  string(name: 'ALERT_ID', value: params.ALERT_ID),
                  string(name: 'EMAIL_FROM', value: params.EMAIL_FROM),
                  string(name: 'EMAIL_SUBJECT', value: params.EMAIL_SUBJECT),
                  text(name: 'EMAIL_BODY', value: params.EMAIL_BODY),
                  string(name: 'MAX_RETRIES', value: params.MAX_RETRIES)
              ]
              // Terminar este build para que el nuevo se encargue
              currentBuild.result = 'SUCCESS'
          }
      }
  }
}


      stage('Generar correo y actualizar Excel') {
          steps {
              script {
                  sh """
                      ${PYTHON_VENV}/bin/python -c "
from utils.email_generator import generate_email_and_excel_fields
from utils.excel_manager import add_alert, close_alert, SHARED_EXCEL_PATH
import os

html, fields = generate_email_and_excel_fields(
  os.environ['SCRIPT_NAME'],
  os.environ['EMAIL_BODY'],
  os.environ['ALERT_TYPE'],
  os.environ.get('ALERT_ID', None)
)

with open('email_body.html', 'w', encoding='utf-8') as f:
  f.write(html)

if os.environ['ALERT_TYPE'] == 'ACTIVA':
  add_alert(fields)
elif os.environ['ALERT_TYPE'] == 'RESUELTA':
  close_alert(fields)
"
                  """

                  archiveArtifacts artifacts: "alertas.xlsx, runs/${params.ALERT_ID}/logs/*.log, runs/${params.ALERT_ID}/screenshots/*.png", allowEmptyArchive: false

                  emailext(
                      subject: "Alerta ${params.ALERT_NAME} (${params.ALERT_TYPE})",
                      body: readFile('email_body.html') + "<p><b>Excel de alertas:</b> <a href='${env.BUILD_URL}artifact/alertas.xlsx'>Ver archivo</a></p>",
                      mimeType: 'text/html',
                      to: "ecommerceoperaciones01@gmail.com"
                  )

                  emailext(
                      subject: "📄 Informe interno - Alerta ${params.ALERT_NAME} (${params.ALERT_TYPE})",
                      body: """<p>Se adjuntan logs y capturas de la ejecución.</p>
                               <p><b>Excel de alertas:</b> <a href='${env.BUILD_URL}artifact/alertas.xlsx'>Ver archivo</a></p>""",
                      mimeType: 'text/html',
                      to: "ecommerceoperaciones01@gmail.com",
                      attachmentsPattern: "runs/${params.ALERT_ID}/logs/*.log, runs/${params.ALERT_ID}/screenshots/*.png, alertas.xlsx"
                  )
              }
          }
      }
  }
}
