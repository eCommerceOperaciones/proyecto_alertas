// Jenkinsfile - Enterprise / Dispatcher-ready
node('main') {

    // ---- Asegurar parámetros del job (si no existen los crea) ----
    // Esto crea SCRIPT_NAME y RETRY_COUNT la primera vez que se ejecuta el job.
    if (!params.SCRIPT_NAME || !params.RETRY_COUNT) {
        properties([
            parameters([
                string(name: 'SCRIPT_NAME', defaultValue: 'acces_frontal_emd', description: 'Nombre lógico del script registrado en dispatcher (ej: acces_frontal_emd)'),
                string(name: 'RETRY_COUNT',  defaultValue: '0',        description: 'Contador de reintentos automáticos (no tocar manualmente normalmente)')
            ])
        ])
    }

    // ---- Credenciales ----
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
                git branch: 'Dev_Sondas', url: 'https://github.com/eCommerceOperaciones/proyecto_alertas.git'
            }

            stage('Preparar entorno') {
              sh '''
                  set -e
                  python3 -m venv venv
                  ./venv/bin/pip install --upgrade pip
                  ./venv/bin/pip install -r requirements.txt

                  # Carpeta local para geckodriver
                  mkdir -p $WORKSPACE/bin

                  # Descargar geckodriver si no existe
                  if [ ! -f "$WORKSPACE/bin/geckodriver" ]; then
                      echo "⚠ geckodriver no encontrado, instalando en $WORKSPACE/bin"
                      GECKO_VERSION="v0.36.0"
                      wget -q https://github.com/mozilla/geckodriver/releases/download/${GECKO_VERSION}/geckodriver-${GECKO_VERSION}-linux64.tar.gz
                      tar -xzf geckodriver-${GECKO_VERSION}-linux64.tar.gz
                      mv geckodriver $WORKSPACE/bin/geckodriver
                      chmod +x $WORKSPACE/bin/geckodriver
                      rm geckodriver-${GECKO_VERSION}-linux64.tar.gz
                  else
                      echo "✅ geckodriver ya está instalado en $WORKSPACE/bin/geckodriver"
                  fi
              '''
            }


            stage('Ejecutar dispatcher / script') {
                script {
                    // Ejecuta el dispatcher runner, pasando el nombre lógico del script
                    // runner.py se encargará de localizar y ejecutar el script real y escribir status.txt
                    def scriptName = params.SCRIPT_NAME ?: 'acces_frontal_emd'
                    echo "▶ Ejecutando runner para SCRIPT_NAME=${scriptName}"
                    sh """set -e
                        ./venv/bin/python src/runner.py --script "${scriptName}" --profile "$WORKSPACE/profiles/selenium_cert" --email-data "$WORKSPACE/email_data.json"
                    """
                }
            }

            stage('Verificar estado') {
                script {
                    // Leer el status que genera el script ejecutado (status.txt en la raíz del workspace)
                    def statusPath = "${WORKSPACE}/status.txt"
                    def status = null

                    if (fileExists(statusPath)) {
                        status = readFile(statusPath).trim()
                        echo "✅ status.txt encontrado: ${status}"
                    } else {
                        // Si no existe status.txt, considerarlo error (más seguro)
                        echo "⚠ status.txt NO encontrado en: ${statusPath}"
                        currentBuild.result = 'FAILURE'
                        error("Fallo: status.txt no generado por el script.")
                    }

                    // Control de reintentos: solo 1 reintento permitido automáticamente
                    def retryCount = 0
                    try {
                        retryCount = params.RETRY_COUNT.toInteger()
                    } catch (e) {
                        retryCount = 0
                    }
                    echo "🔄 RETRY_COUNT actual: ${retryCount}"

                    if (status == "falso_positivo") {

                        if (retryCount >= 1) {
                            echo "ℹ Ya se realizó un reintento. No se volverá a lanzar automáticamente."
                            // dejar éxito y continuar (sin relanzar)
                            currentBuild.result = 'SUCCESS'
                        } else {
                            echo "⚠ Falso positivo detectado. Programando UN único reintento en 5 minutos..."
                            currentBuild.result = 'SUCCESS'   // evitar notificación por ahora

                            // dormir / reintentar
                            sleep(time: 1, unit: "MINUTES")

                            // relanzar el mismo job con RETRY_COUNT incrementado y manteniendo SCRIPT_NAME
                            def nextRetry = (retryCount + 1).toString()
                            echo "▶ Lanzando reintento: RETRY_COUNT=${nextRetry} SCRIPT_NAME=${params.SCRIPT_NAME}"
                            build job: env.JOB_NAME,
                                  parameters: [
                                      string(name: 'RETRY_COUNT', value: nextRetry),
                                      string(name: 'SCRIPT_NAME', value: params.SCRIPT_NAME)
                                  ],
                                  wait: false
                        }

                    } else if (status == "alarma_confirmada") {
                        echo "🚨 Alarma confirmada según status.txt"
                        currentBuild.result = 'FAILURE'
                    } else {
                        echo "⚠ Estado desconocido en status.txt: '${status}'"
                        currentBuild.result = 'FAILURE'
                    }
                }
            }

        } catch (err) {
            currentBuild.result = 'FAILURE'
            echo "❌ Error en la ejecución: ${err}"
        } finally {
            stage('Post - Archivar y Notificar') {
                script {
                    def run_id = ""
                    if (fileExists("${WORKSPACE}/current_run.txt")) {
                        try {
                            run_id = readFile("${WORKSPACE}/current_run.txt").trim()
                        } catch (e) {
                            echo "Warn: no se pudo leer current_run.txt: ${e}"
                        }
                    }

                    // Archivar artefactos si hay run_id
                    if (run_id) {
                        archiveArtifacts artifacts: "runs/${run_id}/**", allowEmptyArchive: true
                    } else {
                        echo "No se encontró current_run.txt; no se archivarán runs/<id> automáticamente"
                    }

                    // Enviar correo solo si hubo alarma confirmada (build marcado como FAILURE)
                    if (currentBuild.result == 'FAILURE') {
                        // Intentar adjuntar artifacts del run si existen
                        def attachments = ""
                        if (run_id) {
                            attachments = "runs/${run_id}/logs/*.log, runs/${run_id}/screenshots/*.png"
                        }

                        emailext(
                            subject: "🚨 Alarma ACCES FRONTAL EMD confirmada",
                            body: """<p>Se ha confirmado la alarma ACCES FRONTAL EMD.</p>
                                     <p>Revisa la carpeta de ejecución para logs y capturas.</p>""",
                            to: "ecommerceoperaciones01@gmail.com",
                            attachmentsPattern: attachments
                        )
                    } else {
                        echo "No se enviará correo (build no marcado como FAILURE)."
                    }
                }
            }
        }
    }
}
