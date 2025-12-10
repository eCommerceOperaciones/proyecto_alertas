FROM jenkins/jenkins:lts

USER root

# Instalar Docker CLI y docker-compose dentro de Jenkins
RUN apt-get update && \
    apt-get install -y docker.io docker-compose && \
    rm -rf /var/lib/apt/lists/*

# Crear grupo docker si no existe y añadir jenkins al grupo
RUN groupadd -f docker && usermod -aG docker jenkins

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
