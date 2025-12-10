pipeline {
    agent any

    environment {
        DOCKER_COMPOSE_FILE = 'docker-compose.yml'
        PWD = pwd()
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
                echo "[INFO] Instalando dependencias Python..."
                sh """
                    docker compose -f ${DOCKER_COMPOSE_FILE} run --rm python-runner \
                    sh -c "
                        echo 'Contenido de /app:' && ls -la /app && \
                        echo 'Contenido de /app/python_runner:' && ls -la /app/python_runner && \
                        pip install --no-cache-dir -r /app/python_runner/requirements.txt
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
} // ← ESTE ES EL QUE TE FALTABA: cierre del pipeline