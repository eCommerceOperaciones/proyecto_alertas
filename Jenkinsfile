pipeline {
    agent any
    parameters {
        string(name: 'SCRIPT_NAME', defaultValue: 'main.py', description: 'Script Python a ejecutar')
    }
    environment {
        EMAIL_USER = credentials('email-alertas-user')
        EMAIL_PASS = credentials('email-alertas-pass')
        JENKINS_USER = credentials('jenkins-api-user')
        JENKINS_TOKEN = credentials('jenkins-api-token')
        JENKINS_URL = 'http://localhost:8080'  // Ajusta según tu entorno
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

                # Crear .env temporal para la ejecución
                cat > .env << EOL
                EMAIL_USER=${EMAIL_USER}
                EMAIL_PASS=${EMAIL_PASS}
                JENKINS_USER=${JENKINS_USER}
                JENKINS_TOKEN=${JENKINS_TOKEN}
                JENKINS_URL=${JENKINS_URL}
                JOB_NAME=${JOB_NAME}
                EOL
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
