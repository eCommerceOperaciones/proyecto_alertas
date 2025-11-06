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

        // ✅ Leer SIEMPRE el archivo raíz generado por main.py
        def statusFile = "${WORKSPACE}/status.txt"
        def status = readFile(statusFile).trim()

        echo "Estado detectado: ${status}"

        if (status == "falso_positivo") {
            echo "✅ Falso positivo detectado. Reintento único en 5 minutos..."
            currentBuild.result = 'SUCCESS'

            sleep(time: 5, unit: "MINUTES")
            build job: env.JOB_NAME, wait: false
        }
        else if (status == "alarma_confirmada") {
            echo "🚨 Alarma REAL confirmada"
            currentBuild.result = 'FAILURE'
        }
        else {
            echo "⚠ Estado desconocido: ${status}"
            currentBuild.result = 'FAILURE'
        }
                }
            }
        }
    }
}
