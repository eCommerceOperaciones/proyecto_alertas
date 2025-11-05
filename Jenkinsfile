pipeline {
    pipeline {
        agent any
        options {
            timestamps()
            buildDiscarder(logRotator(numToKeepStr: '20'))
        }
        stages {
            stage('Checkout') {
                steps {
                    git branch: 'prueba-vscode', url: 'https://github.com/eCommerceOperaciones/proyecto_alertas.git'
                }
            }
            stage('Diagnóstico nodo') {
                steps {
                    // Print useful info about the agent so we can debug missing system deps
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
                    command -v geckodriver || echo "[WARN] geckodriver not found in PATH"
                    geckodriver --version 2>/dev/null || true
                    command -v xvfb-run || echo "[WARN] xvfb-run not found in PATH"
                    '''
                }
            }
            stage('Preparar entorno') {
                steps {
                    // Use POSIX-safe commands and call venv's executables directly to avoid `source` (bash-only)
                    sh '''
                    set -e
                    python3 -m venv venv
                    ./venv/bin/pip install --upgrade pip
                    ./venv/bin/pip install -r requirements.txt
                    '''
                }
            }
            stage('Ejecutar script Selenium') {
                steps {
                    // Run the script with the venv python so no activation is required
                    // Use xvfb-run if available to provide a virtual display for Firefox
                    sh '''
                    set -e
                    if command -v xvfb-run >/dev/null 2>&1; then
                        echo "Using xvfb-run to provide a virtual display"
                        xvfb-run -a ./venv/bin/python src/main.py
                    else
                        echo "xvfb-run not available, running without Xvfb"
                        ./venv/bin/python src/main.py
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
        }
    }
