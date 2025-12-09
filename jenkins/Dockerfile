FROM jenkins/jenkins:lts

USER root

# Instalar Docker CLI dentro de Jenkins para que pueda ejecutar contenedores
RUN apt-get update && \
    apt-get install -y docker.io docker-compose && \
    rm -rf /var/lib/apt/lists/*

# Volver al usuario Jenkins
USER jenkins

# Plugins esenciales para CI/CD y Slack
RUN jenkins-plugin-cli --plugins \
    workflow-aggregator \
    docker-workflow \
    slack \
    credentials-binding \
    git

# Exponer puertos de Jenkins
EXPOSE 8080
EXPOSE 50000

# Jenkins usará el volumen jenkins_home para persistencia
VOLUME /var/jenkins_home
