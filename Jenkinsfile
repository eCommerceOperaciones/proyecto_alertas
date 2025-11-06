node('main') {

    // ✅ Declaramos el parámetro para controlar reintentos (solo si no existe)
    if (!params.RETRY_COUNT) {
        properties([
            parameters([
                string(name: 'RETRY_COUNT', defaultValue: '0', description: 'Número de reintentos del pipeline')
            ])
        ])
    }

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
                    set -e
                    ./venv/bin/python src/main.py "$WORKSPACE/profiles/selenium_cert"
                """
            }

            stage('Verificar estado') {
                script {

                    def statusFile = "${WORKSPACE}/status.txt"
                    def status = readFile(statusFile).trim()

                    echo "✅ Estado detectado: ${status}"
                    echo "🔄 Reintentos realizados: ${params.RETRY_COUNT}"

                    if (status == "falso_positivo") {

                        if (params.RETRY_COUNT.toInteger() >= 1) {
                            echo "✅ Ya se realizó un reintento previamente. No se ejecutará de nuevo."
                            return
                        }

                        echo "⚠ Falso positivo detectado. Programando único reintento en 5 minutos..."

                        currentBuild.result = 'SUCCESS'

                        sleep(time: 5, unit: "MINUTES")

                        build(
                            job: env.JOB_NAME,
                            parameters: [
                                string(name: 'RETRY_COUNT', value: (params.RETRY_COUNT.toInteger() + 1).toString())
                            ],
                            wait: false
                        )
                    }
                    else if (status == "alarma_confirmada") {
                        echo "🚨 Alarma REAL confirmada."
                        currentBuild.result = 'FAILURE'
                    }
                    else {
                        echo "⚠ Estado desconocido: ${status}"
                        currentBuild.result = 'FAILURE'
                    }
                }
            }

        } catch (err) {
            currentBuild.result = 'FAILURE'
            echo "❌ Error: ${err}"

        } finally {

            stage('Post - Archivar y Notificar') {
                def run_id = readFile("${WORKSPACE}/current_run.txt").trim()
                archiveArtifacts artifacts: "runs/${run_id}/**", allowEmptyArchive: true

                if (currentBuild.result == 'FAILURE') {
                    emailext(
                        subject: "🚨 Alarma ACCES FRONTAL EMD confirmada",
                        body: """<p>Se ha confirmado la alarma ACCES FRONTAL EMD.</p>
                                 <p>Revisa la carpeta de ejecución para logs y capturas.</p>""",
                        to: "ecommerceoperaciones01@gmail.com",
                        attachmentsPattern: "runs/${run_id}/logs/*.log, runs/${run_id}/screenshots/*.png"
                    )
                }
            }
        }
    }
}
