// Scripted Pipeline con parámetros y credenciales
properties([
    parameters([
        string(
            name: 'SCRIPT_NAME',
            defaultValue: 'main.py',
            description: 'Script Python a ejecutar'
        )
    ])
])

node('main') {  // Usa el label que configuraste en tu nodo
    withCredentials([
        usernamePassword(
            credentialsId: 'email-alertas-user', // ID correcto del email
            usernameVariable: 'EMAIL_CREDS_USR',
            passwordVariable: 'EMAIL_CREDS_PSW'
        ),
        usernamePassword(
            credentialsId: 'jenkins-api', // ID correcto de la API Jenkins
            usernameVariable: 'JENKINS_CREDS_USR',
            passwordVariable: 'JENKINS_CREDS_PSW'
        )
    ]) {
        try {
            stage('Checkout') {
                git branch: 'prueba-vscode', url: 'https://github.com/eCommerceOperaciones/proyecto_alertas.git'
            }

            stage('Preparar entorno') {
                sh """
                    set -e
                    python3 -m venv venv
                    ./venv/bin/pip install --upgrade pip
                    ./venv/bin/pip install -r requirements.txt

                    cat > .env << EOL
                    EMAIL_USER=${EMAIL_CREDS_USR}
                    EMAIL_PASS=${EMAIL_CREDS_PSW}
                    JENKINS_USER=${JENKINS_CREDS_USR}
                    JENKINS_TOKEN=${JENKINS_CREDS_PSW}
                    JENKINS_URL=http://localhost:8080
                    JOB_NAME=GSIT_alertas
                    EOL
                """
            }

            stage('Ejecutar script') {
                sh """
                    set -e
                    PROFILE_PATH="$WORKSPACE/profiles/selenium_cert"
                    ./venv/bin/python src/${SCRIPT_NAME} "$PROFILE_PATH"
                """
            }

            currentBuild.result = 'SUCCESS'

        } catch (err) {
            currentBuild.result = 'FAILURE'
            echo "❌ Error: ${err}"
        } finally {
            stage('Post - Archivar y Notificar') {
                archiveArtifacts artifacts: 'screenshots/*.png', allowEmptyArchive: true
                archiveArtifacts artifacts: 'logs/*.log', allowEmptyArchive: true

                if (currentBuild.result == 'FAILURE') {
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
    }
}
