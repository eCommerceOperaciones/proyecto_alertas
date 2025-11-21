# GSIT_Alertas – Sistema Corporativo de Gestión Automática de Alertas

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Jenkins](https://img.shields.io/badge/Jenkins-2.x-orange)
![License](https://img.shields.io/badge/License-Internal%20Use-green)

**GSIT_Alertas** es un sistema de automatización corporativa que detecta alertas críticas recibidas por correo electrónico, las valida automáticamente, elimina falsos positivos mediante reintentos inteligentes y escala los incidentes reales a los equipos correspondientes mediante:

- Correo electrónico enriquecido (HTML)
- Actualización automática del Excel corporativo de seguimiento
- Notificaciones inmediatas en Slack

Todo el proceso está orquestado por **Jenkins** y es 100 % trazable gracias a logs detallados y artefactos archivados.

## ✨ Características principales

- ⏱️ **Respuesta inmediata** ante alertas críticas (segundos desde la recepción del mail)
- 🔄 **Reducción drástica de falsos positivos** con lógica de reintentos configurables
- 📊 **Trazabilidad total**: logs estructurados + artefactos guardados en Jenkins
- 📧 **Escalado multicanal**: correo HTML + Excel corporativo + Slack
- 🛠️ **Diseño modular**: añadir nuevos tipos de alertas es tan simple como crear un nuevo script en `/scripts`
- 🔗 **Integración nativa** con Jenkins, Git, IMAP corporativo y Slack

## 🏗 Arquitectura de alto nivel

```text
Correo entrante (IMAP)
        ↓
Jenkins Pipeline (disparado por polling o webhook)
        ↓
email_listener.py → detecta nueva alerta
        ↓
dispatcher → identifica tipo de alerta (registry.py)
        ↓
Ejecuta script correspondiente (scripts/*.py)
        ↓
utils/
 ├─ email_generator.py → genera correo HTML de escalado
 ├─ excel_manager.py   → actualiza Excel corporativo (con bloqueo)
 └─ slack_notifier.py  → envía mensaje enriquecido a Slack
        ↓
Jenkins archiva logs + adjuntos

```

## 📂 Estructura del proyecto
```textGSIT_Alertas/
├── Jenkinsfile                  ← Pipeline declarativo completo
├── .env.example                 ← Plantilla de variables de entorno
├── requirements.txt
└── src/
    ├── email_listener.py        ← Listener IMAP + lógica de polling
    ├── runner.py                ← Punto de entrada para ejecución manual/local
    ├── dispatcher/
    │   ├── registry.py          ← Registro automático de alertas
    │   └── loader.py            ← Carga dinámica de scripts
    ├── scripts/                 ← ¡Aquí van todas las comprobaciones!
    │   ├── acces_frontal_emd.py
    │   ├── ejemplo_otra_alerta.py
    │   └── ...
    └── utils/
    │    ├── email_generator.py   ← Menjo de crear correos
    │    ├── excel_manager.py     ← Manejo seguro de Excel compartido
    │    └── slack_notifier.py    ← Notificaciones Slack
    │  
    ├── mail_template/
         ├── acces_frontal_emd.html   ← Templates HTML para correos 
         └── ...
    
        
        
        
```
## ⚙️ Requisitos previos

Python 3.8 o superior
Jenkins 2.x con plugins: Pipeline, Email Extension, Git (y opcional Generic Webhook Trigger)
Acceso a servidor IMAP corporativo (normalmente puerto 993/SSL)
Webhook de Slack configurado
Ruta de red al Excel corporativo de seguimiento

## 🚀 Instalación y configuración
```Bashgit clone https://git.empresa.com/GSIT/GSIT_Alertas.git
cd GSIT_Alertas
cp .env.example .env
# ← Edita .env con tus credenciales
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

```

## Variables de entorno obligatorias (.env)

```envIMAP_SERVER=imap.empresa.com
IMAP_PORT=993
EMAIL_USER=gsit.alertas@empresa.com
EMAIL_PASS=**********

JENKINS_URL=https://jenkins.empresa.com
JENKINS_USER=svc_gsit
JENKINS_TOKEN=11abcd12345efgh67890ij

SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX

EXCEL_PATH=//servidor/compartido/SEGUIMIENTO_ALERTAS.xlsx
```
## ▶️ Ejecución
Automática (recomendada): Crear un Pipeline Job en Jenkins usando el Jenkinsfile del repositorio.
Manual / pruebas locales:
```Bashsource venv/bin/activate
python src/runner.py

```
## 📈 Beneficios reales

Tiempo de detección-escalado: de 45 min → menos de 3 min
Reducción de falsos positivos: 92 %
Eliminación total de errores en la actualización del Excel
Histórico completo y auditable desde Jenkins

## ➕ Añadir nueva alerta (¡en 5 minutos!)

Crea src/scripts/nueva_alerta_tuya.py siguiendo el patrón existente
El sistema la detecta automáticamente (gracias a registry.py)
¡Listo! Ya está activa para la próxima ejecución

## 🔒 Seguridad

Credenciales solo en .env y Jenkins Credentials
Excel con bloqueo exclusivo + reintentos para evitar corrupción
Cada ejecución tiene un ID único para trazabilidad total


## GSIT_Alertas – Porque cada minuto cuenta cuando hay un incidente crítico.
¿Dudas o nueva alerta? Abre un issue o avisa al equipo GSIT.
