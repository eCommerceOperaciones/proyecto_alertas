pipeline {
    agent any

    environment {
        IMAP_SERVER = 'imap.gmail.com'
        IMAP_PORT = '993'
        WORKSPACE = "${env.WORKSPACE}"
    }

    stages {
        stage('Leer correos') {
            steps {
                // Cargar credenciales de Jenkins (tipo "Username with password")
                withCredentials([usernamePassword(credentialsId: 'email-creds', usernameVariable: 'EMAIL_USER', passwordVariable: 'EMAIL_PASS')]) {
                    sh '''
                        echo "[INFO] Ejecutando email_listener.py..."
                        python3 email_listener.py
                    '''
                }
            }
        }

        stage('Procesar alertas') {
            steps {
                script {
                    def alerts = readJSON file: 'listener_output.json'
                    if (alerts.size() > 0) {
                        echo "[INFO] Se encontraron ${alerts.size()} alertas"
                        alerts.each { alert ->
                            echo "Alerta: ${alert.alert_name} | Tipo: ${alert.alert_type} | ID: ${alert.alert_id}"
                            // Aquí puedes lanzar otros jobs según el script asociado
                            // Ejemplo:
                            // build job: alert.script, parameters: [string(name: 'ALERT_ID', value: alert.alert_id)]
                        }
                    } else {
                        echo "[INFO] No se encontraron alertas"
                    }
                }
            }
        }
    }

    post {
        success {
            echo "[INFO] Pipeline completado correctamente"
        }
        failure {
            echo "[ERROR] Pipeline falló"
        }
        always {
            archiveArtifacts artifacts: 'listener_output.json', fingerprint: true
            archiveArtifacts artifacts: 'email_listener.log', fingerprint: true
        }
    }
}
