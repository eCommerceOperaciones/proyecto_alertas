/*
Jenkinsfile para el proyecto GSIT_Alertas
Autor: Rodrigo Simoes

Este pipeline:
1. Valida parámetros y credenciales.
2. Hace checkout del código.
3. Prepara el entorno Python.
4. Ejecuta el script Selenium correspondiente.
5. Genera correos y actualiza el Excel compartido.
6. Notifica en Slack.
7. Reintenta ejecución si se detecta falso positivo.

Variables clave:
- SCRIPT_NAME: Nombre lógico del script a ejecutar.
- ALERT_ID: Identificador único de la alerta.
- ALERT_TYPE: ACTIVA o RESUELTA.
- MAX_RETRIES: Número máximo de reintentos.
*/

pipeline {
   agent { label 'main' }

   // =========================
   // Parámetros configurables
   // =========================
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

   // =========================
   // Variables de entorno globales
   // =========================
   environment {
       WORKSPACE_BIN = "${WORKSPACE}/bin"
       PYTHON_VENV = "${WORKSPACE}/venv"
       SHARED_EXCEL = "/var/lib/jenkins/shared/alertas.xlsx"
   }

   stages {

       // =========================
       // Validación inicial
       // =========================
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

       // =========================
       // Checkout del código
       // =========================
       stage('Checkout') {
           steps {
               git branch: 'Dev_AREA_PRIVADA', url: 'https://github.com/eCommerceOperaciones/proyecto_alertas.git'
           }
       }

       stage('Instalar GeckoDriver si no existe') {
          steps {
              sh """
                  if ! command -v geckodriver >/dev/null 2>&1; then
                      echo "⚙ Instalando GeckoDriver..."
                      wget -q https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz
                      tar -xzf geckodriver-v0.34.0-linux64.tar.gz
                      sudo mv geckodriver /usr/local/bin/
                      sudo chmod +x /usr/local/bin/geckodriver
                      echo "✅ GeckoDriver instalado en /usr/local/bin"
                  else
                      echo "✅ GeckoDriver ya está instalado"
                  fi
              """
          }
      }

       // =========================
       // Preparar entorno Python
       // =========================
       stage('Preparar entorno') {
           steps {
               sh """
                   python3 -m venv '${PYTHON_VENV}'
                   '${PYTHON_VENV}/bin/pip' install --upgrade pip
                   '${PYTHON_VENV}/bin/pip' install -r requirements.txt
               """
           }
       }

       // =========================
       // Ejecutar script Selenium
       // =========================
       stage('Ejecutar script de alerta') {
           steps {
               withEnv([
                   "ALERT_NAME=${params.ALERT_NAME}",
                   "ALERT_TYPE=${params.ALERT_TYPE}",
                   "ALERT_ID=${params.ALERT_ID}",
                   "EMAIL_FROM=${params.EMAIL_FROM}",
                   "EMAIL_SUBJECT=${params.EMAIL_SUBJECT}",
                   "EMAIL_BODY=${params.EMAIL_BODY}"
               ]) {
                   sh """
                       '${PYTHON_VENV}/bin/python' src/runner.py \
                           --script '${params.SCRIPT_NAME}' \
                           --profile '${WORKSPACE}/profiles/selenium_cert' \
                           --retry '${params.RETRY_COUNT}' \
                           --max-retries '${params.MAX_RETRIES}'
                   """
               }
           }
       }

       // =========================
       // Generar correos y actualizar Excel
       // =========================
       stage('Generar correo y actualizar Excel') {
           steps {
               script {
                   def realAlertId = readFile('current_alert_id.txt').trim()
                   def status = fileExists('status.txt') ? readFile('status.txt').trim() : "desconocido"

                   // Ejecuta script Python para generar HTML y actualizar Excel
                   sh """
                       set +e
                       '${PYTHON_VENV}/bin/python' -c "
from utils.email_generator import generate_email_and_excel_fields
from utils.excel_manager import add_alert, close_alert
import os, traceback

try:
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
except Exception as e:
   print('[WARN] No se pudo actualizar el Excel compartido:', e)
   traceback.print_exc()
"
                       set -e
                   """

                   // Archivar artefactos relevantes
                   archiveArtifacts artifacts: "alertas.xlsx, runs/${realAlertId}/logs/*.log, runs/${realAlertId}/screenshots/*.png", allowEmptyArchive: true

                   // Correo principal
                   emailext(
                       subject: "Alerta ${params.ALERT_NAME} (${params.ALERT_TYPE})",
                       body: readFile('email_body.html'),
                       mimeType: 'text/html',
                       to: "ecommerceoperaciones01@gmail.com"
                   )

                   // Correo interno con adjuntos
                   emailext(
                       subject: "📄 Informe interno - Alerta ${params.ALERT_NAME} (${params.ALERT_TYPE})",
                       body: """<p>Se adjuntan logs y capturas de la ejecución.</p>
                                <p><b>Excel de alertas:</b> <a href='${env.BUILD_URL}artifact/alertas.xlsx'>Ver archivo</a></p>""",
                       mimeType: 'text/html',
                       to: "ecommerceoperaciones01@gmail.com",
                       attachmentsPattern: "runs/${realAlertId}/logs/*.log, runs/${realAlertId}/screenshots/*.png, alertas.xlsx"
                   )
               }
           }
       }

       // =========================
       // Notificación en Slack
       // =========================
       stage('Notificar en Slack') {
           steps {
               script {
                   def realAlertId = readFile('current_alert_id.txt').trim()
                   def status = fileExists('status.txt') ? readFile('status.txt').trim() : "desconocido"

                   // Crear script temporal para enviar mensaje a Slack
                   writeFile file: 'slack_notify.py', text: """
from utils.slack_notifier import send_slack_alert
send_slack_alert(
   alert_id='${realAlertId}',
   alert_name='${params.ALERT_NAME}',
   alert_type='${params.ALERT_TYPE}',
   status='${status}',
   jenkins_url='${env.BUILD_URL}'
)
"""
                   sh "'${PYTHON_VENV}/bin/python' slack_notify.py"
               }
           }
       }

       // =========================
       // Reintento si falso positivo
       // =========================
       stage('Reintento si falso positivo') {
           when {
               expression {
                   return fileExists('status.txt') && readFile('status.txt').trim() == 'falso_positivo' && params.RETRY_COUNT.toInteger() < params.MAX_RETRIES.toInteger()
               }
           }
           steps {
               script {
                   echo "⚠ Falso positivo detectado, reintentando en 5 minutos..."
                   sleep(time: 5, unit: 'MINUTES')
                   def nextRetry = params.RETRY_COUNT.toInteger() + 1
                   build job: env.JOB_NAME, 
                         parameters: [
                             string(name: 'SCRIPT_NAME', value: params.SCRIPT_NAME),
                             string(name: 'RETRY_COUNT', value: nextRetry.toString()),
                             string(name: 'ALERT_NAME', value: params.ALERT_NAME),
                             string(name: 'ALERT_TYPE', value: params.ALERT_TYPE),
                             string(name: 'ALERT_ID', value: params.ALERT_ID),
                             string(name: 'EMAIL_FROM', value: params.EMAIL_FROM),
                             string(name: 'EMAIL_SUBJECT', value: params.EMAIL_SUBJECT),
                             text(name: 'EMAIL_BODY', value: params.EMAIL_BODY),
                             string(name: 'MAX_RETRIES', value: params.MAX_RETRIES)
                         ],
                         wait: false
               }
           }
       }
   }
}
