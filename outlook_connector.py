import msal
import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID     = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID     = os.getenv("TENANT_ID", "consumers")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES    = [
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/User.Read"
]

def get_access_token():
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
    
    # Utiliser le cache si disponible
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            print("✅ Token récupéré depuis le cache")
            return result["access_token"]
    
    # Device Code Flow
    flow = app.initiate_device_flow(scopes=SCOPES)
    print(f"\n👉 {flow['message']}\n")
    result = app.acquire_token_by_device_flow(flow)
    
    if "access_token" in result:
        print("✅ Authentification réussie !")
        return result["access_token"]
    else:
        raise Exception(f"❌ Erreur : {result.get('error_description')}")

def get_emails_non_lus(token, top=10):
    headers = {"Authorization": f"Bearer {token}"}
    url = (
        "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages"
        "?$filter=isRead eq false"
        "&$orderby=receivedDateTime desc"
        f"&$top={top}"
        "&$select=id,subject,from,receivedDateTime,body,isRead,importance"
    )
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        emails = response.json().get("value", [])
        print(f"📬 {len(emails)} email(s) non lu(s) trouvé(s)")
        return emails
    else:
        print(f"❌ Erreur Graph API : {response.status_code}")
        return []

def marquer_lu(token, message_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
    requests.patch(url, headers=headers, json={"isRead": True})

def envoyer_reponse(token, message_id, corps_reponse):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/reply"
    response = requests.post(url, headers=headers, json={"comment": corps_reponse})
    if response.status_code == 202:
        print("✅ Réponse envoyée")
        return True
    else:
        print(f"❌ Erreur envoi : {response.status_code}")
        return False

def get_info_utilisateur(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
    if response.status_code == 200:
        return response.json()
    return {}

print("✅ outlook_connector.py prêt — en attente des credentials Azure")