// Jenkinsfile - Enterprise / Dispatcher-ready
node('main') {

  // ---- Asegurar parámetros del job ----
  if (!params.SCRIPT_NAME || !params.RETRY_COUNT) {
      properties([
          parameters([
              string(name: 'SCRIPT_NAME', defaultValue: 'acces_frontal_emd', description: 'Nombre lógico del script registrado en dispatcher'),
              string(name: 'RETRY_COUNT',  defaultValue: '0', description: 'Contador de reintentos automáticos')
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
              git branch: 'Dev_Sondas', url: 'https://github.com/eCommerceOperaciones/proyecto_alertas.git'
          }

          stage('Preparar entorno') {
              sh '''
                  set -e
                  python3 -m venv venv
                  ./venv/bin/pip install --upgrade pip
                  ./venv/bin/pip install -r requirements.txt

                  mkdir -p $WORKSPACE/bin
                  if [ ! -f "$WORKSPACE/bin/geckodriver" ]; then
                      echo "⚠ geckodriver no encontrado, instalando en $WORKSPACE/bin"
                      GECKO_VERSION="v0.36.0"
                      wget -q bloqueado${GECKO_VERSION}/geckodriver-${GECKO_VERSION}-linux64.tar.gz
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
                  def scriptName = params.SCRIPT_NAME ?: 'acces_frontal_emd'
                  def emailDataPath = ""

                  if (fileExists("${WORKSPACE}/email_data_path.txt")) {
                      emailDataPath = readFile("${WORKSPACE}/email_data_path.txt").trim()
                  } else {
                      error("❌ No se encontró email_data_path.txt. No se puede ejecutar el script sin datos del correo.")
                  }

                  echo "▶ Ejecutando runner para SCRIPT_NAME=${scriptName}"
                  sh """set -e
                      ./venv/bin/python src/runner.py --script "${scriptName}" --profile "$WORKSPACE/profiles/selenium_cert" --email-data "${emailDataPath}"
                  """
              }
          }

          stage('Verificar estado') {
              script {
                  def statusPath = "${WORKSPACE}/status.txt"
                  def status = null

                  if (fileExists(statusPath)) {
                      status = readFile(statusPath).trim()
                      echo "✅ status.txt encontrado: ${status}"
                  } else {
                      echo "⚠ status.txt NO encontrado en: ${statusPath}"
                      currentBuild.result = 'FAILURE'
                      error("Fallo: status.txt no generado por el script.")
                  }

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
                          currentBuild.result = 'SUCCESS'
                      } else {
                          echo "⚠ Falso positivo detectado. Programando UN único reintento en 1 minuto..."
                          currentBuild.result = 'SUCCESS'
                          sleep(time: 1, unit: "MINUTES")
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

                  if (run_id) {
                      archiveArtifacts artifacts: "runs/${run_id}/**", allowEmptyArchive: true
                  } else {
                      echo "No se encontró current_run.txt; no se archivarán runs/<id> automáticamente"
                  }

                  if (currentBuild.result == 'FAILURE') {
                      if (params.SCRIPT_NAME == 'acces_frontal_emd') {
                          emailext(
                              subject: "🚨 Alarma ACCES FRONTAL EMD confirmada",
                              body: "<p>Se ha confirmado la alarma ACCES FRONTAL EMD.</p><p>Revisa la carpeta de ejecución para logs y capturas.</p>",
                              to: "ecommerceoperaciones01@gmail.com",
                              attachmentsPattern: run_id ? "runs/${run_id}/logs/*.log, runs/${run_id}/screenshots/*.png" : ""
                          )
                      } else if (params.SCRIPT_NAME == '01_carrega_url_wsdl') {
                          emailext(
                              subject: "🚨 Alarma 01_carrega_url_wsdl confirmada",
                              body: "<p>Se ha confirmado la alarma 01_carrega_url_wsdl.</p><p>Revisa la carpeta de ejecución para logs y capturas.</p>",
                              to: "ecommerceoperaciones01@gmail.com",
                              attachmentsPattern: run_id ? "runs/${run_id}/logs/*.log, runs/${run_id}/screenshots/*.png" : ""
                          )
                      } else {
                          emailext(
                              subject: "❌ Error técnico en ejecución de script",
                              body: "<p>El script ${params.SCRIPT_NAME} falló por error técnico.</p><p>Revisa los logs para más detalles.</p>",
                              to: "ecommerceoperaciones01@gmail.com"
                          )
                      }
                  } else {
                      echo "No se enviará correo (build no marcado como FAILURE)."
                  }
              }
          }
      }
  }
}
