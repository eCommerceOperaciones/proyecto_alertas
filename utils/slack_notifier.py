import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def send_slack_alert(alert_id, alert_name, alert_type, status, jenkins_url=None):
   if not SLACK_WEBHOOK_URL:
       print("[WARN] SLACK_WEBHOOK_URL no configurado, no se enviará mensaje a Slack.")
       return False

   color = "#36a64f" if status == "falso_positivo" else "#ff0000"

   payload = {
       "attachments": [
           {
               "fallback": f"Alerta {alert_name} ({alert_type}) - {status}",
               "color": color,
               "title": f"🚨 Alerta {alert_name} ({alert_type})",
               "fields": [
                   {"title": "ID", "value": alert_id, "short": True},
                   {"title": "Estado", "value": status, "short": True}
               ],
               "footer": "GSIT_Alertas",
               "ts": int(__import__("time").time())
           }
       ]
   }

   if jenkins_url:
       payload["attachments"][0]["fields"].append(
           {"title": "Jenkins", "value": f"<{jenkins_url}|Ver ejecución>", "short": False}
       )

   try:
       resp = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
       if resp.status_code == 200:
           print("[INFO] Mensaje enviado a Slack correctamente.")
           return True
       else:
           print(f"[ERROR] Fallo al enviar mensaje a Slack: {resp.status_code} - {resp.text}")
           return False
   except Exception as e:
       print(f"[ERROR] Excepción enviando mensaje a Slack: {e}")
       return False
