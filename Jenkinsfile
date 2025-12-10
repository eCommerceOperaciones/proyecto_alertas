pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout([$class: 'GitSCM',
                    branches: [[name: '*/main']], // Cambia a tu rama real
                    userRemoteConfigs: [[
                        url: 'git@github.com:eCommerceOperaciones/proyecto_alertas.git',
                        credentialsId: 'SSH-JENKINS'
                    ]]
                ])
            }
        }

        stage('Leer correos') {
            steps {
                withCredentials([
                    file(credentialsId: 'config-env-file', variable: 'ENV_FILE'),
                    string(credentialsId: 'EMAIL_USER', variable: 'EMAIL_USER'),
                    string(credentialsId: 'EMAIL_PASS', variable: 'EMAIL_PASS')
                ]) {
                    sh '''
                        echo "[INFO] Cargando archivo .env desde credenciales..."
                        cp "$ENV_FILE" .env
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
                            // Aquí podrías llamar Selenium o otro Job
                        }
                    } else {
                        echo "[INFO] No se encontraron alertas"
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: '**/*.json, **/*.log', fingerprint: true
        }
        success {
            echo "[INFO] Pipeline completado correctamente"
        }
        failure {
            echo "[ERROR] Pipeline falló"
        }
    }
}
