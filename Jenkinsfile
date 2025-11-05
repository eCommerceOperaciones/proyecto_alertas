pipeline {
    agent any
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
        }
    }
}
