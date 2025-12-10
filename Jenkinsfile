pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                checkout([$class: 'GitSCM',
                    branches: [[name: '*/Dev_AREA_PRIVADA']],
                    userRemoteConfigs: [[
                        url: 'git@github.com:eCommerceOperaciones/proyecto_alertas.git',
                        credentialsId: 'SSH-JENKINS'
                    ]]
                ])
            }
        }
        stage('Leer correos') {
            steps {
                withCredentials([
                    file(credentialsId: 'config-env-file', variable: 'ENV_FILE'),
                    string(credentialsId: 'EMAIL_USER', variable: 'EMAIL_USER'),
                    string(credentialsId: 'EMAIL_PASS', variable: 'EMAIL_PASS')
                ]) {
                    sh '''
                        cp "$ENV_FILE" .env
                        python3 email_listener.py
                    '''
                }
            }
        }
        stage('Procesar alertas') {
            steps {
                script {
                    def alerts = readJSON file: 'listener_output.json'
                    if (alerts.size() > 0) {
                        echo "Se encontraron ${alerts.size()} alertas"
                    } else {
                        echo "No se encontraron alertas"
                    }
                }
            }
        }
    }
}
