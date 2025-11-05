pipeline {
    agent any
<<<<<<< HEAD
    options {
        timestamps() // logs con hora
        buildDiscarder(logRotator(numToKeepStr: '20')) // mantener solo últimos 20 builds
    }
    stages {
        stage('Preparar entorno') {
            steps {
                sh '''
                cd ~/proyectos/proyecto_alertas
                python3 -m venv venv
                source venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }
        stage('Ejecutar script Selenium') {
            steps {
                sh '''
                cd ~/proyectos/proyecto_alertas
                source venv/bin/activate
                python src/main.py
                '''
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'screenshots/*.png', allowEmptyArchive: true
            archiveArtifacts artifacts: 'logs/*.log', allowEmptyArchive: true
=======

    environment {
        IMAGE_NAME = "alertas_selenium"
        IMAGE_TAG = "${env.GIT_COMMIT}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${IMAGE_NAME}:${IMAGE_TAG}", "--cache-from=${IMAGE_NAME}:latest .")
                }
            }
        }

        stage('Run Container') {
            steps {
                script {
                    docker.image("${IMAGE_NAME}:${IMAGE_TAG}").inside('-u root --shm-size=2g') {
                        sh 'python3 src/main.py'
                    }
                }
            }
        }

        stage('Guardar artefactos') {
            steps {
                archiveArtifacts artifacts: 'captura.png', fingerprint: true
            }
        }

        stage('Actualizar imagen cacheada') {
            steps {
                sh "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest"
            }
>>>>>>> b3c70078362b015fb9d98843b130e925d2b9fdd8
        }
    }
}
