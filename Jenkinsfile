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
            git branch: 'Dev_Sondas', url: 'https://github.com/eCommerceOperaciones/proyecto_alertas.git''
        }
    }
    stage('Preparar entorno') {
        steps {
            sh '''
                set -e
                python3 -m venv ${PYTHON_VENV}
                ${PYTHON_VENV}/bin/pip install --upgrade pip
                ${PYTHON_VENV}/bin/pip install -r requirements.txt
                mkdir -p ${WORKSPACE_BIN}
                if [ ! -f "${WORKSPACE_BIN}/geckodriver" ]; then
                    echo "Instalando geckodriver..."
                    GECKO_VERSION="v0.36.0"
                    wget -q "https://github.com/mozilla/geckodriver/releases/download/${GECKO_VERSION}/geckodriver-${GECKO_VERSION}-linux64.tar.gz""
                    tar -xzf geckodriver-${GECKO_VERSION}-linux64.tar.gz
                    mv geckodriver ${WORKSPACE_BIN}/geckodriver
                    chmod +x ${WORKSPACE_BIN}/geckodriver
                    rm geckodriver-${GECKO_VERSION}-linux64.tar.gz
                else
                    echo "✅ geckodriver ya instalado."
                fi
            '''
        }
    }
    stage('Ejecutar script') {
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
                    ${PYTHON_VENV}/bin/python src/runner.py \
                        --script ${params.SCRIPT_NAME} \
                        --profile "$WORKSPACE/profiles/selenium_cert" \
                        --retry ${params.RETRY_COUNT} \
                        --max-retries ${params.MAX_RETRIES}
                """
            }
        }
    }
    stage('Verificar resultado') {
        steps {
            script {
                def statusPath = "${WORKSPACE}/status.txt"
                if (!fileExists(statusPath)) {
                    error("Fallo: status.txt no generado por el script.")
                }
                def status = readFile(statusPath).trim()
                echo "Estado detectado: ${status}"
                def retryCount = params.RETRY_COUNT.toInteger()
                def maxRetries = params.MAX_RETRIES.toInteger()

                if (status == "falso_positivo") {
                    if (retryCount >= maxRetries) {
                        echo "Máximo de reintentos alcanzado. Enviando correo interno de cierre..."
                        emailext(
                            subject: "🔍 Informe interno - Alerta ${params.ALERT_NAME} revisada dos veces (Falso Positivo)",
                            body: """<p>La alerta fue revisada dos veces y se determinó como FALSO POSITIVO.</p>""",
                            mimeType: 'text/html',
                            to: "eecommerceoperaciones01@gmail.com.com",
                            attachmentsPattern: "runs/**/logs/*.log, runs/**/screenshots/*.png"
                        )
                    } else {
                        echo "Programando reintento..."
                        sleep(time: 5, unit: "MINUTES")
                        build job: env.JOB_NAME,
                            parameters: [
                                string(name: 'RETRY_COUNT', value: (retryCount + 1).toString()),
                                string(name: 'SCRIPT_NAME', value: params.SCRIPT_NAME),
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
                } else if (status == "alarma_confirmada") {
                    echo "🚨 Alarma confirmada, procediendo a envío de correos y actualización de Excel..."
                } else {
                    error("Estado desconocido: ${status}")
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
from utils.excel_manager import add_alert, close_alert
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
                emailext(
                    subject: "Alerta ${params.ALERT_NAME} (${params.ALERT_TYPE})",
                    body: readFile('email_body.html'),
                    mimeType: 'text/html',
                    to: "correo_interno@dominio.com"
                )
                emailext(
                    subject: "📄 Informe interno - Alerta ${params.ALERT_NAME} (${params.ALERT_TYPE})",
                    body: """<p>Se adjuntan logs y capturas de la ejecución.</p>""",
                    mimeType: 'text/html',
                    to: "ecommerceoperaciones01@gmail.com",
                    attachmentsPattern: "runs/**/logs/*.log, runs/**/screenshots/*.png"
                )
            }
        }
    }
}
post {
    always {
        script {
            def run_id = fileExists("${WORKSPACE}/current_run.txt") ? readFile("${WORKSPACE}/current_run.txt").trim() : ""
            if (run_id) {
                archiveArtifacts artifacts: "runs/${run_id}/**", allowEmptyArchive: true
            }
        }
    }
    failure {
        script {
            emailext(
                subject: "❌ Error técnico en ejecución de ${params.SCRIPT_NAME}",
                body: """<p>El script <b>${params.SCRIPT_NAME}</b> falló por error técnico.</p>
                         <p><b>Log de Jenkins:</b> <a href="${env.BUILD_URL}console">${env.BUILD_URL}console</a></p>""",
                mimeType: 'text/html',
                to: "ecommerceoperaciones01@gmail.com"
            )
        }
    }
}
}
