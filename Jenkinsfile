pipeline {
    agent any

    environment {
        WORKSPACE = "${env.WORKSPACE}"
        EMAIL_DATA_PATH_FILE = "${WORKSPACE}/email_data_path.txt"
        CURRENT_RUN_FILE = "${WORKSPACE}/current_run.txt"
    }

    stages {

        stage('Validar archivos del Listener') {
            steps {
                script {
                    if (!fileExists(env.EMAIL_DATA_PATH_FILE)) {
                        error "❌ No existe email_data_path.txt en el workspace: ${env.EMAIL_DATA_PATH_FILE}"
                    }

                    if (!fileExists(env.CURRENT_RUN_FILE)) {
                        error "❌ No existe current_run.txt en el workspace: ${env.CURRENT_RUN_FILE}"
                    }

                    echo "✅ Archivos necesarios detectados."
                }
            }
        }

        stage('Leer archivo email_data_path.txt') {
            steps {
                script {
                    env.EMAIL_JSON_PATH = readFile(env.EMAIL_DATA_PATH_FILE).trim()
                    echo "📄 Ruta del email_data.json recibida: ${env.EMAIL_JSON_PATH}"

                    if (!fileExists(env.EMAIL_JSON_PATH)) {
                        error "❌ El archivo email_data.json NO existe en: ${env.EMAIL_JSON_PATH}"
                    }
                }
            }
        }

        stage('Leer datos del JSON') {
            steps {
                script {
                    def jsonText = readFile(env.EMAIL_JSON_PATH)
                    def json = new groovy.json.JsonSlurper().parseText(jsonText)

                    echo "✅ JSON cargado correctamente."

                    // Exportar a variables de entorno (si las necesitas)
                    env.ALERT_NAME = json.alert_name ?: "undefined_alert"
                    env.FROM_EMAIL = json.from_email ?: "undefined_email"
                    env.EMAIL_SUBJECT = json.subject ?: "undefined_subject"
                    env.EMAIL_BODY = json.body ?: "undefined_body"

                    echo "🔔 ALERTA: ${env.ALERT_NAME}"
                    echo "📧 Desde: ${env.FROM_EMAIL}"
                }
            }
        }

        stage('Ejecutar Listener Dispatcher') {
            steps {
                script {
                    echo "🚀 Ejecutando listener_dispatcher.py..."

                    sh """
                        python3 listener_dispatcher.py \\
                        --alert "${env.ALERT_NAME}" \\
                        --from "${env.FROM_EMAIL}" \\
                        --subject "${env.EMAIL_SUBJECT}" \\
                        --body "${env.EMAIL_BODY}"
                    """
                }
            }
        }

    }

    post {
        always {
            echo "✅ Pipeline finalizado."
        }
    }
}
