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
    SHARED_EXCEL = "${WORKSPACE}/alertas.xlsx"
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

    stage('Generar correo y actualizar Excel') {
        steps {
            script {
                def realAlertId = readFile('current_alert_id.txt').trim()

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

                archiveArtifacts artifacts: "alertas.xlsx, runs/${realAlertId}/logs/*.log, runs/${realAlertId}/screenshots/*.png", allowEmptyArchive: true

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
                    attachmentsPattern: "runs/${realAlertId}/logs/*.log, runs/${realAlertId}/screenshots/*.png, alertas.xlsx"
                )
            }
        }
    }
}
}
