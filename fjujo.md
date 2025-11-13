## 📊 Flujo del Proyecto

```mermaid
flowchart TD
   A[📧 Email entrante] -->|IMAP Listener| B[email_listener.py]
   B -->|Detecta alerta y extrae datos| C{Coincide con alerta configurada?}
   C -- No --> Z[❌ Ignorar correo]
   C -- Sí --> D[Lanza Job en Jenkins con parámetros]
   
   subgraph Jenkins Pipeline
       D --> E[Stage: Validar parámetros y credenciales]
       E --> F[Stage: Checkout código]
       F --> G[Stage: Preparar entorno Python]
       G --> H[Stage: Ejecutar script de alerta (runner.py)]
       H -->|Limpia carpeta runs/ALERT_ID| I[Script Selenium específico]
       I -->|Guarda capturas, logs, status.txt| J[runner.py lee resultado]
       J --> K{Resultado}
       K -- falso_positivo --> L[Stage: Reintento si falso positivo]
       L -->|Espera 5 min y relanza job| H
       K -- alarma_confirmada --> M[Stage: Generar correo y actualizar Excel]
       M -->|add_alert o close_alert| N[Excel compartido con filelock]
       M --> O[Correo principal a destinatarios]
       M --> P[Correo interno con logs y capturas]
       M --> Q[Stage: Notificar en Slack]
   end

   Q --> R[📲 Mensaje en canal Slack con ID, estado y enlace a Jenkins]
   N --> S[📊 Histórico centralizado de alertas]
   O --> T[📩 Notificación a usuarios]
   P --> U[📩 Notificación interna con adjuntos]