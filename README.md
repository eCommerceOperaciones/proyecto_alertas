# GSIT_Alertas

**Autor:** Rodrigo Pinheiro Simoes
**Proyecto:** GSIT_Alertas  
**Fecha:** 6 de noviembre de 2025

---

## 📌 Descripción del Proyecto
GSIT_Alertas es un sistema automatizado que realiza validaciones mediante Selenium. Se ejecuta el script principal que lee las alertas via correo y el pipeline identifica la alerta basado en el cuerpo del correo ,se ejecuta desde Jenkins y detecta si existe una **alarma confirmada** o un **falso positivo**, enviando notificaciones por correo electrónico y gestionando reintentos controlados.

El objetivo principal del proyecto es gestionar las alertas de GSIT automaticamente correctamente, generando alertas solo cuando es estrictamente necesario y evitando notificaciones falsas.

---

## ✅ Características principales
- Automatización completa 100% headless con **Selenium + Python**.
- Gestión de certificados y flujos internos del portal para gestionar alertas de GSIT.
- Sistema de **detección inteligente de falso positivo**.
- Reintentos controlados desde Jenkins utilizando **parámetros persistidos**.
- Registro de estados mediante `status.txt`.
- Capturas de pantalla automáticas.
- Envío de correo con logs y artefactos adjuntos.

---

## 🧱 Estructura del Proyecto
```
GSIT_Alertas/
├── Jenkinsfile
├── requirements.txt
├── src/
│   ├── main.py
│   ├── email_listener.py
├── profiles/
│   └── selenium_cert/
├── runs/
│   └── {yyyyMMdd_hhmmss}/screenshots
└── status.txt (generado en cada ejecución)
```

---

## 🚀 Flujo de Trabajo (Pipeline)
### 1. **Checkout del repositorio**
Jenkins obtiene la rama configurada desde GitHub y prepara el workspace.

### 2. **Preparación del entorno Python**
- Creación de entorno virtual.
- Instalación de dependencias desde `requirements.txt`.

### 3. **Ejecución de Selenium**
El script principal realiza:
- acceso al portal
- selección de certificado
- navegación por las distintas secciones
- validación de documentos

Tras finalizar, genera un archivo `status.txt` con uno de estos valores:
- `falso_positivo`
- `alarma_confirmada`

### 4. **Lectura del estado**
Jenkins analiza `status.txt` y determina el comportamiento:
- Si es **falso positivo** → espera 5 minutos y hace un único reintento.
- Si es **alarma confirmada** → marca FALLA.

### 5. **Reintentos controlados**
Se utiliza un parámetro persistente en Jenkins:
```
RETRY_COUNT
```
- `0` = primera ejecución
- `1` = reintento
- `>=2` = NO reintentar más

### 6. **Notificación por Email**
Al finalizar, el pipeline envía correo con:
- estado final
- capturas de pantalla
- archivos generados

---

## ⚙️ Configuración
### Variables utilizadas (en Jenkins o `.env`)
- `EMAIL_CREDS_USR`
- `EMAIL_CREDS_PSW`
- `ACCES_FRONTAL_EMD_URL`
- `PROFILE_PATH`

### Dependencias Python
```
selenium==4.18.1
webdriver-manager==4.0.1
imapclient
beautifulsoup4==4.12.2
python-dotenv==1.0.1
```

---

## 📬 Notificación por correo
El pipeline envía un email automático cuando:
- se detecta una alarma confirmada
- finaliza el reintento de validación con error.

El correo incluye:
✅ Mensaje con resultado  
✅ Logs de ejecución  
✅ Capturas generadas en `/runs/.../screenshots/`  

---

## 🛠 Mantenimiento y Buenas Prácticas
- Mantener Selenium y WebDriver actualizados.
- Limpiar periódicamente la carpeta `runs/`.
- Mantener los parámetros del pipeline en Jenkins.
- Validar que los selectores CSS/XPath no se rompen tras cambios del portal.

---

## ✨ Futuras mejoras
- Dashboard gráfico con estado histórico de alertas.
- Integración con Slack/Teams.
- Reemplazo opcional de Selenium por Playwright.
- Logs distribuidos centralizados.

---

## 👤 Autor
**Rodrigo**

Proyecto creado para automatización de ejecucion de procedimientos basados en alertas de entorno GSIT.

