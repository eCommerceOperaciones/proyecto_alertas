/*
================================================================================
 Jenkinsfile – Pipeline para el proyecto GSIT_Alertas
 Autor: Rodrigo Simoes

 Descripción general:
 --------------------
 Este pipeline orquesta el ciclo de ejecución de scripts asociados al sistema
 de Alertas (GSIT). Automatiza:

  - Validación de parámetros y credenciales.
  - Preparación del entorno Python (venv + dependencias).
  - Ejecución de scripts de alerta para casos ACTIVOS o RESUELTOS.
  - Gestión de estados (status.txt).
  - Generación de correo interno + externo.
  - Actualización del Excel compartido con nuevas alertas o cierres.
  - Archivado de artefactos: logs, capturas, Excel.
  - Notificación hacia Slack.
  - Manejo automático de reintentos ante falsos positivos.

 Este pipeline está preparado para ejecutarse en agentes etiquetados como "main".

================================================================================
*/

pipeline {

    /* -------------------------------------------------------------------------
       Selección del agente Jenkins donde correrá el pipeline
       ------------------------------------------------------------------------- */
    agent { label 'main' }


    /* -------------------------------------------------------------------------
       Parámetros configurables del job
       ------------------------------------------------------------------------- */
    parameters {
        string(name: 'SCRIPT_NAME',    defaultValue: '', description: 'Nombre lógico del script registrado en dispatcher')
        string(name: 'RETRY_COUNT',    defaultValue: '0', description: 'Contador de reintentos automáticos')
        string(name: 'ALERT_NAME',     defaultValue: '', description: 'Nombre de la alerta detectada')
        string(name: 'ALERT_TYPE',     defaultValue: '', description: 'Tipo de alerta: ACTIVA o RESUELTA')
        string(name: 'ALERT_ID',       defaultValue: '', description: 'ID de la alerta en Excel (opcional)')
        string(name: 'EMAIL_FROM',     defaultValue: '', description: 'Remitente del correo')
        string(name: 'EMAIL_SUBJECT',  defaultValue: '', description: 'Asunto del correo')
        text(  name: 'EMAIL_BODY',     defaultValue: '', description: 'Contenido del correo (HTML o texto plano)')
        string(name: 'MAX_RETRIES',    defaultValue: '1', description: 'Número máximo de reintentos permitidos')
    }


    /* -------------------------------------------------------------------------
       Variables de entorno para rutas internas
       ------------------------------------------------------------------------- */
    environment {
        WORKSPACE_BIN = "${WORKSPACE}/bin"
        PYTHON_VENV   = "${WORKSPACE}/venv"
        SHARED_EXCEL  = "/var/lib/jenkins/shared/alertas.xlsx"   // Ruta centralizada del Excel corporativo
    }


    /* -------------------------------------------------------------------------
       Definición de las etapas del pipeline
       ------------------------------------------------------------------------- */
    stages {


        /* ---------------------------------------------------------------------
           Asignación de nombre y descripción al build
           --------------------------------------------------------------------- */
        stage('Set Build Name') {
            steps {
                script {
                    currentBuild.displayName = "#${env.BUILD_NUMBER} - ALERT_ID: ${params.ALERT_ID}"
                    currentBuild.description = "Alerta detectada: ${params.ALERT_NAME} (Tipo: ${params.ALERT_TYPE})"
                }
            }
        }


        /* ---------------------------------------------------------------------
           Validación de parámetros obligatorios y carga de credenciales
           --------------------------------------------------------------------- */
        stage('Validar parámetros y credenciales') {
            steps {
                script {
                    if (!params.SCRIPT_NAME || !params.ALERT_NAME) {
                        error("Parámetros críticos faltantes: SCRIPT_NAME y ALERT_NAME son obligatorios.")
                    }
                }

                // Carga segura de credenciales
                withCredentials([
                    usernamePassword(
                        credentialsId: 'email-alertas-user',
                        usernameVariable: 'EMAIL_CREDS_USR',
                        passwordVariable: 'EMAIL_CREDS_PSW'
                    ),
                    usernamePassword(
                        credentialsId: 'jenkins-api',
                        usernameVariable: 'JENKINS_CREDS_USR',
                        passwordVariable: 'JENKINS_CREDS_PSW'
                    )
                ]) {
                    echo "✅ Credenciales cargadas correctamente."
                }
            }
        }


        /* ---------------------------------------------------------------------
           Descarga del repositorio con los scripts del proyecto
           --------------------------------------------------------------------- */
        stage('Checkout') {
            steps {
                git branch: 'Dev_AREA_PRIVADA',
                    url: 'https://github.com/eCommerceOperaciones/proyecto_alertas.git'
            }
        }


        /* ---------------------------------------------------------------------
           Preparación del entorno de ejecución (Python + dependencias)
           --------------------------------------------------------------------- */
        stage('Preparar entorno') {
            steps {
                script {

                    // Limpieza de archivos antiguos asociados a la alerta
                    if (params.ALERT_ID) {
                        sh "find runs/${params.ALERT_ID} -type f -mmin +5 -exec rm -rf {} + || true"
                    }
                }

                // Creación y actualización del entorno virtual Python
                sh """
                    python3 -m venv '${PYTHON_VENV}'
                    '${PYTHON_VENV}/bin/pip' install --upgrade pip
                    '${PYTHON_VENV}/bin/pip' install -r requirements.txt
                """
            }
        }


        /* ---------------------------------------------------------------------
           Ejecución del script de alerta (solo para ALERTA ACTIVA)
           --------------------------------------------------------------------- */
        stage('Ejecutar script de alerta') {
            when {
                expression { params.ALERT_TYPE == 'ACTIVA' }
            }
            steps {

                // Exportación de parámetros como variables de entorno
                withEnv([
                    "ALERT_NAME=${params.ALERT_NAME}",
                    "ALERT_TYPE=${params.ALERT_TYPE}",
                    "ALERT_ID=${params.ALERT_ID}",
                    "EMAIL_FROM=${params.EMAIL_FROM}",
                    "EMAIL_SUBJECT=${params.EMAIL_SUBJECT}",
                    "EMAIL_BODY=${params.EMAIL_BODY}"
                ]) {

                    // Ejecución controlada del runner Python
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


        /* ---------------------------------------------------------------------
           Lectura del estado generado por el script (status.txt)
           --------------------------------------------------------------------- */
        stage('Leer estado de ejecución') {
            steps {
                script {
                    def statusFile = "${WORKSPACE}/status.txt"

                    if (fileExists(statusFile)) {
                        env.ALERT_STATUS = readFile(statusFile).trim()
                        echo "Estado leído: ${env.ALERT_STATUS}"
                    } else {
                        env.ALERT_STATUS = "desconocido"
                        echo "⚠ No se encontró status.txt, se asume estado 'desconocido'"
                    }
                }
            }
        }


        /* ---------------------------------------------------------------------
           Gestión del Excel + generación de correos internos y externos
           --------------------------------------------------------------------- */
        stage('Generar correo y actualizar Excel') {
            steps {
                script {

                    // ID real de la alerta generada o actualizada
                    def realAlertId = readFile('current_alert_id.txt').trim()
                    def status = fileExists('status.txt') ? readFile('status.txt').trim() : "desconocido"

                    /* -------------------------------------------------------------
                       Ejecución de módulo Python: genera HTML del correo y
                       actualiza el Excel corporativo.
                    ------------------------------------------------------------- */
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
        os.environ.get('ALERT_ID')
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

                    // Copia del Excel para archivarlo como artefacto
                    sh "cp ${SHARED_EXCEL} alertas.xlsx"


                    /* -------------------------------------------------------------
                       Lógica para determinar si debe enviarse correo
                    ------------------------------------------------------------- */
                    def enviarCorreo = false

                    if (params.ALERT_TYPE == 'RESUELTA') {
                        enviarCorreo = true

                    } else if (status != 'falso_positivo') {
                        enviarCorreo = true

                    } else if (params.RETRY_COUNT.toInteger() >= params.MAX_RETRIES.toInteger()) {
                        enviarCorreo = true
                    }


                    /* -------------------------------------------------------------
                       Envío de correos + archivado de artefactos
                    ------------------------------------------------------------- */
                    if (enviarCorreo) {

                        if (params.ALERT_TYPE == 'ACTIVA') {

                            archiveArtifacts artifacts: 
                                "alertas.xlsx, runs/${realAlertId}/logs/*.log, runs/${realAlertId}/screenshots/*.png",
                                allowEmptyArchive: true

                            emailext(
                                subject: "📄 ${params.ALERT_NAME} ${params.ALERT_ID} ${status} - Interno",
                                body: """
                                <p>Se adjuntan logs y capturas de la ejecución.</p>
                                <p><b>Excel de alertas:</b> 
                                <a href='${env.BUILD_URL}artifact/alertas.xlsx'>Descargar archivo</a></p>
                                """,
                                mimeType: 'text/html',
                                to: "ecommerceoperaciones01@gmail.com",
                                attachmentsPattern: "runs/${realAlertId}/logs/*.log, runs/${realAlertId}/screenshots/*.png, alertas.xlsx"
                            )

                        } else {

                            archiveArtifacts artifacts: "alertas.xlsx", allowEmptyArchive: true

                            emailext(
                                subject: "📄 ${params.ALERT_NAME} ${params.ALERT_ID} ${status} - Interno",
                                body: """
                                <p>Alerta resuelta. No se adjuntan capturas ni logs de Selenium.</p>
                                <p><b>Excel de alertas:</b> 
                                <a href='${env.BUILD_URL}artifact/alertas.xlsx'>Descargar archivo</a></p>
                                """,
                                mimeType: 'text/html',
                                to: "ecommerceoperaciones01@gmail.com",
                                attachmentsPattern: "alertas.xlsx"
                            )
                        }

                        // Segunda notificación (correo externo al equipo)
                        emailext(
                            subject: "Alerta ${params.ALERT_NAME} (${params.ALERT_TYPE})",
                            body: readFile('email_body.html'),
                            mimeType: 'text/html',
                            to: "ecommerceoperaciones01@gmail.com"
                        )

                    } else {
                        echo "⏩ No se envía correo todavía: se espera reintento por posible falso positivo."
                    }
                }
            }
        }


        /* ---------------------------------------------------------------------
           Notificación hacia Slack (solo si aplica)
           --------------------------------------------------------------------- */
        stage('Notificar en Slack') {
            when {
                expression {
                    return params.ALERT_TYPE == 'RESUELTA' ||
                           env.ALERT_STATUS != 'falso_positivo' ||
                           params.RETRY_COUNT.toInteger() >= params.MAX_RETRIES.toInteger()
                }
            }
            steps {
                script {

                    // Escape seguro del contenido del correo
                    def safeEmailBody = groovy.json.JsonOutput.toJson(params.EMAIL_BODY)

                    // Script Python dinámico para enviar alerta a Slack
                    def slackScript = """
from utils.slack_notifier import send_slack_alert

email_body = ${safeEmailBody}

send_slack_alert(
    alert_id='${params.ALERT_ID}',
    alert_name='${params.ALERT_NAME}',
    alert_type='${params.ALERT_TYPE}',
    status='${env.ALERT_STATUS}',
    email_body=email_body,
    jenkins_url='${env.BUILD_URL}'
)
"""

                    writeFile file: 'slack_notify.py', text: slackScript
                    sh "'${PYTHON_VENV}/bin/python' slack_notify.py"
                }
            }
        }


        /* ---------------------------------------------------------------------
           Reintento automático en caso de falso positivo
           --------------------------------------------------------------------- */
        stage('Reintento si falso positivo') {
            when {
                expression {
                    return params.ALERT_TYPE == 'ACTIVA' &&
                           env.ALERT_STATUS == 'falso_positivo' &&
                           params.RETRY_COUNT.toInteger() < params.MAX_RETRIES.toInteger()
                }
            }
            steps {
                script {

                    echo "⚠ Falso positivo detectado, reintentando en 5 minutos..."

                    sleep(time: 5, unit: 'MINUTES')

                    def nextRetry = params.RETRY_COUNT.toInteger() + 1

                    // Nuevo build con incremento del contador de reintentos
                    build job: env.JOB_NAME,
                          parameters: [
                              string(name: 'SCRIPT_NAME', value: params.SCRIPT_NAME),
                              string(name: 'RETRY_COUNT', value: nextRetry.toString()),
                              string(name: 'ALERT_NAME',  value: params.ALERT_NAME),
                              string(name: 'ALERT_TYPE',  value: params.ALERT_TYPE),
                              string(name: 'ALERT_ID',    value: params.ALERT_ID),
                              string(name: 'EMAIL_FROM',  value: params.EMAIL_FROM),
                              string(name: 'EMAIL_SUBJECT', value: params.EMAIL_SUBJECT),
                              text(  name: 'EMAIL_BODY', value: params.EMAIL_BODY),
                              string(name: 'MAX_RETRIES', value: params.MAX_RETRIES)
                          ],
                          wait: false
                }
            }
        }
    }
}
