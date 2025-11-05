pipeline {
    agent any
    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }
    parameters {
        string(name: 'SCRIPT_NAME', defaultValue: 'main.py', description: 'Script Python a ejecutar')
    }
    stages {
        stage('Checkout') {
            steps {
                git branch: 'prueba-vscode', url: 'https://github.com/eCommerceOperaciones/proyecto_alertas.git'
            }
        }
        stage('Diagnóstico nodo') {
            steps {
                sh '''
                set -e
                echo "=== Nodo info ==="
                echo "User: $(whoami)"
                echo "CWD: $(pwd)"
                echo "Shell: ${SHELL:-/bin/sh}"
                echo
                echo "=== Python / venv ==="
                python3 --version || true
                python3 -m venv --help >/dev/null 2>&1 || echo "[WARN] python3-venv may be missing"
                echo
                echo "=== Binaries ==="
                command -v firefox || echo "[WARN] firefox not found in PATH"
                firefox --version 2>/dev/null || true
                command -v xvfb-run || echo "[WARN] xvfb-run not found in PATH"
                '''
            }
        }
        stage('Preparar entorno') {
            steps {
                sh '''
                set -e
                python3 -m venv venv
                ./venv/bin/pip install --upgrade pip
                ./venv/bin/pip install -r requirements.txt
                '''
            }
        }
        stage('Ejecutar script Python') {
            steps {
                sh '''
                set -e
                PROFILE_PATH="$WORKSPACE/profiles/selenium_cert"
                if command -v xvfb-run >/dev/null 2>&1; then
                    echo "Using xvfb-run to provide a virtual display"
                    xvfb-run -a ./venv/bin/python src/${SCRIPT_NAME} "$PROFILE_PATH"
                else
                    echo "xvfb-run not available, running without Xvfb"
                    ./venv/bin/python src/${SCRIPT_NAME} "$PROFILE_PATH"
                fi
                '''
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'screenshots/*.png', allowEmptyArchive: true
            archiveArtifacts artifacts: 'logs/*.log', allowEmptyArchive: true
        }
        failure {
            emailext(
                subject: "❌ Fallo en ejecución ${SCRIPT_NAME}",
                body: """<p>El job ha fallado ejecutando <b>${SCRIPT_NAME}</b>.</p>
                         <p>Revisa el log adjunto y las capturas.</p>""",
                to: "destinatario@dominio.com",
                attachmentsPattern: "logs/*.log, screenshots/*.png"
            )
        }
    }
}
