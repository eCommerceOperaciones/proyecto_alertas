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
                checkout scm
            }
        }

        stage('Verificar workspace') {
            steps {
                echo "[INFO] Directorio actual: ${env.WORKSPACE}"
                sh 'ls -la'
            }
        }

        stage('Instalar dependencias Python') {
            steps {
                echo "[INFO] Instalando dependencias Python..."
                sh """
                    docker compose -f ${DOCKER_COMPOSE_FILE} run --rm python-runner \
                    sh -c "
                        echo '=== CONTENIDO DE /app ===' && ls -la /app && \
                        cat /app/requirements.txt
                        pip install --no-cache-dir -r /app/requirements.txt
                    "
                """
            }
        }

        stage('Procesar alertas') {
            steps {
                echo "[INFO] Ejecutando script principal..."
                sh """
                    docker compose -f ${DOCKER_COMPOSE_FILE} run --rm python-runner \
                    python /app/src/main.py
                """
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
            echo "[INFO] Archivando artefactos..."
            archiveArtifacts artifacts: '**/output/**', allowEmptyArchive: true
        }
    }
}
