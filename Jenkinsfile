pipeline {
    agent any
    environment {
        DOCKER_COMPOSE_FILE = 'docker-compose.yml'
    }
    stages {
        stage('Cleanup') {
            steps {
                echo "[INFO] Limpiando workspace..."
                deleteDir()
            }
        }
        stage('Checkout') {
            steps {
                echo "[INFO] Clonando repositorio..."
                checkout([$class: 'GitSCM', branches: [[name: '*/Dev_AREA_PRIVADA']], doGenerateSubmoduleConfigurations: false, extensions: [], userRemoteConfigs: [[url: 'git@repo.git']]], quiet: true)
            }
        }
        stage('Procesar alertas') {
            steps {
                echo "[INFO] Ejecutando script principal..."
                withCredentials([
                    string(credentialsId: 'EMAIL_USER', variable: 'EMAIL_USER'),
                    string(credentialsId: 'EMAIL_PASS', variable: 'EMAIL_PASS')
                ]) {
                    sh '''
                        docker compose -f docker-compose.yml run --rm \
                          -e EMAIL_USER="$EMAIL_USER" \
                          -e EMAIL_PASS="$EMAIL_PASS" \
                          python-runner \
                          sh -c "pip install --no-cache-dir --quiet --disable-pip-version-check --root-user-action=ignore -r /app/GSIT_Alertas/01-Email_Listener/python-runner/requirements.txt > /dev/null && \
                                 echo '[INFO] Dependencias instaladas correctamente' && \
                                 python /app/GSIT_Alertas/01-Email_Listener/src/email_listener.py"
                    '''
                }
            }
        }
    }
    post {
        success {
            echo "[SUCCESS] Pipeline completado correctamente."
        }
        failure {
            echo "[ERROR] Pipeline falló."
        }
        always {
            script {
                if (fileExists('output')) {
                    archiveArtifacts artifacts: '**/output/**', allowEmptyArchive: true
                } else {
                    echo "[INFO] No se encontraron artefactos para archivar."
                }
            }
        }
    }
}
