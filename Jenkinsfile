pipeline {
    agent any
    parameters {
        string(name: 'SCRIPT_NAME', defaultValue: 'main.py', description: 'Script Python a ejecutar')
    }
    stages {
        stage('Checkout') {
            steps {
                git branch: 'prueba-vscode', url: 'https://github.com/eCommerceOperaciones/proyecto_alertas.git'
            }
        }
        stage('Preparar entorno') {
            steps {
                sh '''
                set -e
                python3 -m venv venv
                ./venv/bin/pip install --upgrade pip
                ./venv/bin/pip install -r requirements.txt
                '''
            }
        }
        stage('Ejecutar script') {
            steps {
                sh '''
                set -e
                PROFILE_PATH="$WORKSPACE/profiles/selenium_cert"
                ./venv/bin/python src/${SCRIPT_NAME} "$PROFILE_PATH"
                '''
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'screenshots/*.png', allowEmptyArchive: true
            archiveArtifacts artifacts: 'logs/*.log', allowEmptyArchive: true
        }
        failure {
            emailext(
                subject: "❌ Fallo en ejecución ${SCRIPT_NAME}",
                body: """<p>El job ha fallado ejecutando <b>${SCRIPT_NAME}</b>.</p>
                         <p>Revisa el log adjunto y las capturas.</p>""",
                to: "destinatario@dominio.com",
                attachmentsPattern: "logs/*.log, screenshots/*.png"
            )
        }
    }
}
