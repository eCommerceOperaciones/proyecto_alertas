# Imagen base oficial de Jenkins LTS
FROM jenkins/jenkins:lts

# Cambiar a usuario root para instalar dependencias
USER root

# Instalar Docker CLI y docker-compose
RUN apt-get update && \
    apt-get install -y docker.io docker-compose && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copiar lista de plugins y instalarlos
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# Exponer puertos de Jenkins
EXPOSE 8080
EXPOSE 50000

# Volumen para persistencia de datos
VOLUME /var/jenkins_home

# Mantener usuario root para evitar problemas de permisos con docker.sock
USER root
