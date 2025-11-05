pipeline {
    agent any
    options {
pipeline {
    agent any
    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }
    stages {
        stage('Checkout') {
            steps {
                git branch: 'prueba-vscode', url: 'https://github.com/eCommerceOperaciones/proyecto_alertas.git'
            }
            steps {
                // Use POSIX-safe commands and call venv's executables directly to avoid `source` (bash-only)
                sh '''
                set -e
                python3 -m venv venv
                ./venv/bin/pip install --upgrade pip
                ./venv/bin/pip install -r requirements.txt
                '''
            }
        }
        stage('Ejecutar script Selenium') {
            steps {
                // Run the script with the venv python so no activation is required
                sh '''
                set -e
                ./venv/bin/python src/main.py
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
