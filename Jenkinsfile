pipeline {
    agent any

    environment {
        DOCKER_COMPOSE_FILE = 'docker-compose.yml'
        WORKSPACE_PATH = '/var/jenkins_home/workspace/GSIT_Alertas/01-Email_Listener'
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
                        url: 'https://github.com/eCommerceOperaciones/proyecto_alertas.git',
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
                echo "[INFO] Instalando dependencias en python-runner..."
                sh """
                    docker compose -f ${DOCKER_COMPOSE_FILE} run --rm python-runner \
                    ls -la /app/python_runner && \
                    docker compose -f ${DOCKER_COMPOSE_FILE} run --rm python-runner \
                    pip install -r /app/python_runner/requirements.txt
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

        stage('Verificar requirements') {
            steps {
                sh """
                    docker compose run --rm python-runner ls -la /app/python_runner
                """
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
