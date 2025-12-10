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
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: 'origin/Dev_AREA_PRIVADA']],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [],
                    userRemoteConfigs: [[
                        url: 'bloqueado',
                        credentialsId: 'SSH-JENKINS'
                    ]]
                ])
            }
        }

        stage('Verificar workspace') {
            steps {
                echo "[INFO] Directorio actual: ${pwd()}"
                sh 'ls -la'
            }
        }

        stage('Instalar dependencias Python') {
            steps {
                echo "[INFO] Verificando y instalando dependencias..."
                sh """
                    docker compose -f ${DOCKER_COMPOSE_FILE} run --rm python-runner \
                    sh -c 'ls -la /app/python_runner && pip install -r /app/python_runner/requirements.txt'
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
