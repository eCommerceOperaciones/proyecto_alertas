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
                """
            }

            stage('Verificar variables de entorno') {
                sh 'echo "ACCES_FRONTAL_EMD_URL=$ACCES_FRONTAL_EMD_URL"'
            }

            stage('Ejecutar script') {
                sh """
                    set +e
                    ./venv/bin/python src/main.py "$WORKSPACE/profiles/selenium_cert"
                    EXIT_CODE=$?
                    echo "Python exit code: \$EXIT_CODE"
                    exit \$EXIT_CODE
                """
            }

            // ← QUITADO 'steps {}'
            stage('Verificar estado') {
                script {
                    def rootStatus = "${WORKSPACE}/status.txt"
                    if (!fileExists(rootStatus)) {
                        error("No se encontró status.txt en la raíz")
                    }

                    def status = readFile(rootStatus).trim()
                    echo "Estado: ${status}"

                    if (status == "falso_positivo") {
                        currentBuild.result = 'SUCCESS'
                        echo "Falso positivo. Reintentando en 5 min..."
                        sleep(time: 5, unit: 'MINUTES')
                        build job: env.JOB_NAME, wait: false, quietPeriod: 10
                    } else if (status == "alarma_confirmada") {
                        currentBuild.result = 'FAILURE'
                    } else {
                        currentBuild.result = 'FAILURE'
                        error("Estado desconocido: ${status}")
                    }
                }
            }
        } catch (err) {
            currentBuild.result = 'FAILURE'
            echo "Error: ${err}"
        } finally {
            stage('Post - Archivar y Notificar') {
                def run_id = readFile("${WORKSPACE}/current_run.txt").trim()
                archiveArtifacts artifacts: "runs/${run_id}/**", allowEmptyArchive: true

                if (currentBuild.result == 'FAILURE') {
                    emailext(
                        subject: "Alarma ACCES FRONTAL EMD confirmada",
                        body: "<p>Alarma REAL. Revisar logs y capturas.</p>",
                        to: "ecommerceoperaciones01@gmail.com",
                        attachmentsPattern: "runs/${run_id}/logs/*.log, runs/${run_id}/screenshots/*.png"
                    )
                } else {
                    echo "Falso positivo. Sin email."
                }
            }
        }
    }
}