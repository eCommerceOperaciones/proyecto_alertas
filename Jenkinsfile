
# =========================
# Jenkinsfile (actualizado para opción 1)
# =========================
// Jenkinsfile - Enterprise / Dispatcher-ready
node('main') {

  // ---- Asegurar parámetros del job ----
  if (!params.SCRIPT_NAME || !params.RETRY_COUNT) {
      properties([
          parameters([
              string(name: 'SCRIPT_NAME', defaultValue: 'acces_frontal_emd', description: 'Nombre lógico del script registrado en dispatcher'),
              string(name: 'RETRY_COUNT',  defaultValue: '0', description: 'Contador de reintentos automáticos'),
              string(name: 'ALERT_NAME',   defaultValue: '', description: 'Nombre de la alerta detectada'),
              string(name: 'EMAIL_FROM',   defaultValue: '', description: 'Remitente del correo'),
              string(name: 'EMAIL_SUBJECT', defaultValue: '', description: 'Asunto del correo'),
              text(name: 'EMAIL_BODY', defaultValue: '', description: 'Contenido del correo')
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
              '''
          }

          stage('Crear email_data.json dinámico') {
              script {
                  def runId = new Date().format('yyyyMMdd_HHmmss')
                  def runDir = "${WORKSPACE}/runs/${runId}"

                  sh "mkdir -p ${runDir}"

                  def jsonData = [
                      alert_name: params.ALERT_NAME,
                      from_email: params.EMAIL_FROM,
                      subject: params.EMAIL_SUBJECT,
                      body: params.EMAIL_BODY
                  ]

                  writeFile file: "${runDir}/email_data.json", text: groovy.json.JsonOutput.prettyPrint(groovy.json.JsonOutput.toJson(jsonData))
                  writeFile file: "${WORKSPACE}/email_data_path.txt", text: "${runDir}/email_data.json"
                  writeFile file: "${WORKSPACE}/current_run.txt", text: runId
              }
          }

          stage('Ejecutar dispatcher / script') {
              script {
                  def scriptName = params.SCRIPT_NAME ?: 'acces_frontal_emd'

                  if (!fileExists("${WORKSPACE}/email_data_path.txt")) {
                      error("❌ No existe email_data_path.txt")
                  }

                  def emailDataPath = readFile("${WORKSPACE}/email_data_path.txt").trim()

                  if (!fileExists(emailDataPath)) {
                      error("❌ Falta email_data.json en: ${emailDataPath}")
                  }

                  sh """
                      set -e
                      ./venv/bin/python src/runner.py --script "${scriptName}" --profile "$WORKSPACE/profiles/selenium_cert" --email-data "${emailDataPath}"
                  """
              }
          }

          stage('Verificar estado') {
              script {
                  def statusPath = "${WORKSPACE}/status.txt"

                  if (!fileExists(statusPath)) {
                      currentBuild.result = 'FAILURE'
                      error("Falta status.txt")
                  }

                  def status = readFile(statusPath).trim()
                  def retryCount = params.RETRY_COUNT.toInteger()

                  if (status == "falso_positivo") {
                      if (retryCount >= 1) {
                          currentBuild.result = 'SUCCESS'
                      } else {
                          currentBuild.result = 'SUCCESS'
                          sleep(time: 1, unit: 'MINUTES')
                          build job: env.JOB_NAME,
                                parameters: [
                                    string(name: 'RETRY_COUNT', value: (retryCount + 1).toString()),
                                    string(name: 'SCRIPT_NAME', value: params.SCRIPT_NAME)
                                ],
                                wait: false
                      }
                  } else if (status == "alarma_confirmada") {
                      currentBuild.result = 'FAILURE'
                  } else {
                      currentBuild.result = 'FAILURE'
                  }
              }
          }

      } catch (err) {
          currentBuild.result = 'FAILURE'
          error("Pipeline detenido: ${err}")
      } finally {
          stage('Post - Archivar') {
              script {
                  def run_id = fileExists("${WORKSPACE}/current_run.txt") ? readFile("${WORKSPACE}/current_run.txt").trim() : ""

                  if (run_id) {
                      archiveArtifacts artifacts: "runs/${run_id}/**", allowEmptyArchive: true
                  }
              }
          }
      }
  }
}
