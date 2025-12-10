pipeline {
    agent any

    environment {
        DOCKER_COMPOSE_FILE = 'docker-compose.yml'
        EMAIL_USER = credentials('EMAIL_USER')  // ID de credencial en Jenkins
        EMAIL_PASS = credentials('EMAIL_PASS')  // ID de credencial en Jenkins
    }

    stages {
        stage('Cleanup') {
            steps {
                echo "[INFO] Limpiando workspace..."
                deleteDir()
            }
        }

        stage('Procesar alertas') {
            steps {
                echo "[INFO] Ejecutando script principal..."
                sh """
                    docker compose -f ${DOCKER_COMPOSE_FILE} run --rm \
                    -e EMAIL_USER=${EMAIL_USER} \
                    -e EMAIL_PASS=${EMAIL_PASS} \
                    python-runner sh -c "
                        pip install --no-cache-dir -r /app/GSIT_Alertas/01-Email_Listener/python-runner/requirements.txt && \
                        python /app/GSIT_Alertas/01-Email_Listener/src/email_listener.py
                    "
                """
            }
        }
    
    } // ← cierre de stages

    post {
        success {
            echo "[SUCCESS] Pipeline completado correctamente."
        }
        failure {
            echo "[ERROR] Pipeline falló."
        }
        always {
            echo "[INFO] Archivando artefactos..."
            archiveArtifacts artifacts: '**/output/**', allowEmptyArchive: true
        }
    }
} // ← cierre de pipeline
