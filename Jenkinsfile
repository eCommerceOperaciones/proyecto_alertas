node('main') {
  if (!params.SCRIPT_NAME || !params.RETRY_COUNT) {
      properties([
          parameters([
              string(name: 'SCRIPT_NAME', defaultValue: 'acces_frontal_emd', description: 'Nombre lógico del script registrado en dispatcher'),
              string(name: 'RETRY_COUNT',  defaultValue: '0', description: 'Contador de reintentos automáticos')
          ])
      ])
  }

  withCredentials([
      usernamePassword(credentialsId: 'email-alertas-user', usernameVariable: 'EMAIL_CREDS_USR', passwordVariable: 'EMAIL_CREDS_PSW'),
      usernamePassword(credentialsId: 'jenkins-api', usernameVariable: 'JENKINS_CREDS_USR', passwordVariable: 'JENKINS_CREDS_PSW')
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
                  if (!fileExists("${WORKSPACE}/email_data_path.txt")) {
                      error("❌ No se encontró email_data_path.txt. No se puede ejecutar el script sin datos del correo.")
                  }
                  def emailDataPath = readFile("${WORKSPACE}/email_data_path.txt").trim()
                  if (!fileExists(emailDataPath)) {
                      error("❌ El archivo email_data.json no existe en: ${emailDataPath}")
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
                  if (!fileExists(statusPath)) {
                      currentBuild.result = 'FAILURE'
                      error("Fallo: status.txt no generado por el script.")
                  }
                  def status = readFile(statusPath).trim()
                  echo "✅ status.txt encontrado: ${status}"

                  def retryCount = params.RETRY_COUNT.toInteger()
                  echo "🔄 RETRY_COUNT actual: ${retryCount}"

                  if (status == "falso_positivo") {
                      if (retryCount >= 1) {
                          echo "ℹ Ya se realizó un reintento. No se volverá a lanzar automáticamente."
                          currentBuild.result = 'SUCCESS'
                      } else {
                          echo "⚠ Falso positivo detectado. Programando UN único reintento en 1 minuto..."
                          currentBuild.result = 'SUCCESS'
                          sleep(time: 1, unit: "MINUTES")
                          build job: env.JOB_NAME,
                                parameters: [
                                    string(name: 'RETRY_COUNT', value: (retryCount + 1).toString()),
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
          error("Pipeline detenido por error crítico")
      } finally {
          if (currentBuild.result == 'FAILURE' && !fileExists("${WORKSPACE}/status.txt")) {
              echo "⚠ Fallo antes de ejecutar el script. No se enviará correo ni se archivarán artefactos."
              return
          }
          stage('Post - Archivar y Notificar') {
              script {
                  def run_id = fileExists("${WORKSPACE}/current_run.txt") ? readFile("${WORKSPACE}/current_run.txt").trim() : ""
                  if (run_id) {
                      archiveArtifacts artifacts: "runs/${run_id}/**", allowEmptyArchive: true
                  }
                  if (currentBuild.result == 'FAILURE') {
                      emailext(
                          subject: "🚨 Alarma ${params.SCRIPT_NAME} confirmada",
                          body: "<p>Se ha confirmado la alarma ${params.SCRIPT_NAME}.</p><p>Revisa la carpeta de ejecución para logs y capturas.</p>",
                          to: "ecommerceoperaciones01@gmail.com",
                          attachmentsPattern: run_id ? "runs/${run_id}/logs/*.log, runs/${run_id}/screenshots/*.png" : ""
                      )
                  } else {
                      echo "No se enviará correo (build no marcado como FAILURE)."
                  }
              }
          }
      }
  }
}
