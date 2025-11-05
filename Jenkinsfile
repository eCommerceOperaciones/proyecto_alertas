properties([
    parameters([
        string(
            name: 'SCRIPT_NAME',
            defaultValue: 'main.py',
            description: 'Script Python a ejecutar'
        )
    ])
])

node('main') {
    withCredentials([
        usernamePassword(
            credentialsId: 'email-alertas-user',
            usernameVariable: 'EMAIL_CREDS_USR',
            passwordVariable: 'EMAIL_CREDS_PSW'
        ),
        usernamePassword(
            credentialsId: 'jenkins-api',
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
                    ./venv/bin/python src/${SCRIPT_NAME} "$WORKSPACE/profiles/selenium_cert"
                """
            }

            currentBuild.result = 'SUCCESS'

        } catch (err) {
            currentBuild.result = 'FAILURE'
            echo "❌ Error: ${err}"
        } finally {
            stage('Post - Archivar y Notificar') {
                archiveArtifacts artifacts: 'runs/**', allowEmptyArchive: true

                if (currentBuild.result == 'FAILURE') {
                    emailext(
                        subject: "❌ Fallo en ejecución ${SCRIPT_NAME}",
                        body: """<p>Elemento no encontrado tras reintento.</p>
                                 <p>Revisa la carpeta de ejecución para logs y capturas.</p>""",
                        to: "ecommerceoperaciones01@gmail.com",
                        attachmentsPattern: "runs/**/logs/*.log, runs/**/screenshots/*.png"
                    )
                }
            }
        }
    }
}
