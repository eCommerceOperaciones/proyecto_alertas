// Jenkinsfile - Pipeline optimizado para ejecución de scripts de alerta
pipeline {
  agent { label 'main' }

  parameters {
      string(name: 'SCRIPT_NAME', defaultValue: 'acces_frontal_emd', description: 'Nombre lógico del script registrado en dispatcher')
      string(name: 'RETRY_COUNT', defaultValue: '0', description: 'Contador de reintentos automáticos')
      string(name: 'ALERT_NAME', defaultValue: '', description: 'Nombre de la alerta detectada')
      string(name: 'EMAIL_FROM', defaultValue: '', description: 'Remitente del correo')
      string(name: 'EMAIL_SUBJECT', defaultValue: '', description: 'Asunto del correo')
      text(name: 'EMAIL_BODY', defaultValue: '', description: 'Contenido del correo')
      string(name: 'MAX_RETRIES', defaultValue: '1', description: 'Número máximo de reintentos permitidos')
  }

  environment {
      WORKSPACE_BIN = "${WORKSPACE}/bin"
      PYTHON_VENV = "${WORKSPACE}/venv"
  }

  stages {
      stage('Validar parámetros y credenciales') {
          steps {
              script {
                  if (!params.SCRIPT_NAME || !params.ALERT_NAME) {
                      error("Parámetros críticos faltantes: SCRIPT_NAME y ALERT_NAME son obligatorios.")
                  }
              }
              withCredentials([
                  usernamePassword(credentialsId: 'email-alertas-user', usernameVariable: 'EMAIL_CREDS_USR', passwordVariable: 'EMAIL_CREDS_PSW'),
                  usernamePassword(credentialsId: 'jenkins-api', usernameVariable: 'JENKINS_CREDS_USR', passwordVariable: 'JENKINS_CREDS_PSW')
              ]) {
                  echo "✅ Credenciales cargadas correctamente."
              }
          }
      }

      stage('Checkout') {
          steps {
              git branch: 'Dev_Sondas', url: 'https://github.com/eCommerceOperaciones/proyecto_alertas.git'
          }
      }

      stage('Preparar entorno') {
          steps {
              sh '''
                  set -e
                  python3 -m venv ${PYTHON_VENV}
                  ${PYTHON_VENV}/bin/pip install --upgrade pip
                  ${PYTHON_VENV}/bin/pip install -r requirements.txt

                  mkdir -p ${WORKSPACE_BIN}
                  if [ ! -f "${WORKSPACE_BIN}/geckodriver" ]; then
                      echo "Instalando geckodriver..."
                      GECKO_VERSION="v0.36.0"
                      wget -q "https://github.com/mozilla/geckodriver/releases/download/${GECKO_VERSION}/geckodriver-${GECKO_VERSION}-linux64.tar.gz"
                      tar -xzf geckodriver-${GECKO_VERSION}-linux64.tar.gz
                      mv geckodriver ${WORKSPACE_BIN}/geckodriver
                      chmod +x ${WORKSPACE_BIN}/geckodriver
                      rm geckodriver-${GECKO_VERSION}-linux64.tar.gz
                  else
                      echo "✅ geckodriver ya instalado."
                  fi
              '''
          }
      }

      stage('Ejecutar script') {
          steps {
              withEnv([
                  "ALERT_NAME=${params.ALERT_NAME}",
                  "EMAIL_FROM=${params.EMAIL_FROM}",
                  "EMAIL_SUBJECT=${params.EMAIL_SUBJECT}",
                  "EMAIL_BODY=${params.EMAIL_BODY}"
              ]) {
                  sh """
                      ${PYTHON_VENV}/bin/python src/runner.py \
                          --script ${params.SCRIPT_NAME} \
                          --profile "$WORKSPACE/profiles/selenium_cert" \
                          --retry ${params.RETRY_COUNT}
                  """
              }
          }
      }

      stage('Verificar resultado') {
          steps {
              script {
                  def statusPath = "${WORKSPACE}/status.txt"
                  if (!fileExists(statusPath)) {
                      error("Fallo: status.txt no generado por el script.")
                  }
                  def status = readFile(statusPath).trim()
                  echo "Estado detectado: ${status}"

                  def retryCount = params.RETRY_COUNT.toInteger()
                  def maxRetries = params.MAX_RETRIES.toInteger()

                  if (status == "falso_positivo") {
                      if (retryCount >= maxRetries) {
                          echo "Máximo de reintentos alcanzado. No se relanzará."
                      } else {
                          echo "Programando reintento..."
                          build job: env.JOB_NAME,
                              parameters: [
                                  string(name: 'RETRY_COUNT', value: (retryCount + 1).toString()),
                                  string(name: 'SCRIPT_NAME', value: params.SCRIPT_NAME),
                                  string(name: 'ALERT_NAME', value: params.ALERT_NAME),
                                  string(name: 'EMAIL_FROM', value: params.EMAIL_FROM),
                                  string(name: 'EMAIL_SUBJECT', value: params.EMAIL_SUBJECT),
                                  text(name: 'EMAIL_BODY', value: params.EMAIL_BODY),
                                  string(name: 'MAX_RETRIES', value: params.MAX_RETRIES)
                              ],
                              wait: false
                      }
                  } else if (status == "alarma_confirmada") {
                      error("🚨 Alarma confirmada.")
                  } else {
                      error("Estado desconocido: ${status}")
                  }
              }
          }
      }
  }

  post {
      always {
          script {
              def run_id = fileExists("${WORKSPACE}/current_run.txt") ? readFile("${WORKSPACE}/current_run.txt").trim() : ""
              if (run_id) {
                  archiveArtifacts artifacts: "runs/${run_id}/**", allowEmptyArchive: true
              }
          }
      }
      failure {
          script {
              def status = fileExists("${WORKSPACE}/status.txt") ? readFile("${WORKSPACE}/status.txt").trim() : "sin_status"
              if (status == "alarma_confirmada") {
                  def htmlBody = sh(
                      script: """
                          SCRIPT_NAME=${params.SCRIPT_NAME} \
                          EMAIL_BODY="${params.EMAIL_BODY.replace('"','\\"')}" \
                          ${PYTHON_VENV}/bin/python utils/generate_email.py
                      """,
                      returnStdout: true
                  ).trim()
                  emailext(
                      subject: "🚨 Alarma ${params.SCRIPT_NAME} confirmada",
                      body: htmlBody,
                      mimeType: 'text/html',
                      to: "ecommerceoperaciones01@gmail.com"
                  )
              } else {
                  emailext(
                      subject: "❌ Error técnico en ejecución de ${params.SCRIPT_NAME}",
                      body: """<p>El script <b>${params.SCRIPT_NAME}</b> falló por error técnico.</p>
                               <p><b>Log de Jenkins:</b> <a href="${env.BUILD_URL}console">${env.BUILD_URL}console</a></p>""",
                      mimeType: 'text/html',
                      to: "ecommerceoperaciones01@gmail.com"
                  )
              }
          }
      }
  }
}
