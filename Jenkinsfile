pipeline {
    agent any
    parameters {
        string(name: 'SCRIPT_NAME', defaultValue: 'main.py', description: 'Script Python a ejecutar')
    }
    environment {
        EMAIL_CREDS = credentials('email-alertas')
        JENKINS_CREDS = credentials('jenkins-api')
        JENKINS_URL = 'http://localhost:8080'
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

                cat > .env << EOL
                EMAIL_USER=${EMAIL_CREDS_USR}
                EMAIL_PASS=${EMAIL_CREDS_PSW}
                JENKINS_USER=${JENKINS_CREDS_USR}
                JENKINS_TOKEN=${JENKINS_CREDS_PSW}
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
                to: "ecommerceoperaciones01@gmail.com",
                attachmentsPattern: "logs/*.log, screenshots/*.png"
            )
        }
    }
}
