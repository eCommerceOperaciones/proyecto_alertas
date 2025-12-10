pipeline {
    agent any

    options {
        skipDefaultCheckout()
    }

    stages {

        stage('Cleanup') {
            steps {
                deleteDir()
            }
        }

        stage('Checkout') {
            steps {
                checkout scm
                sh 'ls -la'
            }
        }

        stage('Verificar workspace') {
            steps {
                echo "[INFO] Directorio actual: ${env.WORKSPACE}"
                sh 'ls -la'
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
                        rm -f .env
                        cp "$ENV_FILE" .env

                        docker-compose run --rm python-runner pip install -r /app/python_runner/requirements.txt
                        docker-compose run --rm python-runner python3 /app/src/email_listener.py
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
