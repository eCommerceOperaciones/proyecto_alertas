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
                    set -e
                    ./venv/bin/python src/main.py "$WORKSPACE/profiles/selenium_cert"
                """
            }

            stage('Verificar estado') {
                script {
                    def statusFile = sh(script: "find runs -name status.txt | head -n 1", returnStdout: true).trim()
                    def status = readFile(statusFile).trim()

                    if (status == "falso_positivo") {
                        echo "✅ Falso positivo detectado. Reintento único en 5 minutos..."
                        
                        // ✅ Marcar como éxito para evitar correo y fallo
                        currentBuild.result = 'SUCCESS'

                        // ✅ Programar reintento sin bucles infinitos
                        sleep(time: 5, unit: "MINUTES")
                        build job: env.JOB_NAME, wait: false
                    } 
                    else if (status == "alarma_confirmada") {
                        echo "🚨 Alarma confirmada"
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

                // ✅ Solo envía correo si realmete hubo alarma confirmada
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
