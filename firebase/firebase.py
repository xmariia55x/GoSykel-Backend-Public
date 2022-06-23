
import firebase_admin
from firebase_admin import credentials, auth

CERTIFICATE = {
  "type": "complete",
  "project_id": "complete",
  "private_key_id": "complete",
  "private_key": "complete",
  "client_email": "complete",
  "client_id": "complete",
  "auth_uri": "complete",
  "token_uri": "complete",
  "auth_provider_x509_cert_url": "complete",
  "client_x509_cert_url": "complete"
}

cred = credentials.Certificate(CERTIFICATE)
firebase_admin.initialize_app(cred)
def delete_firebase_user_by_email(email):
    user = auth.get_user_by_email(email)
    auth.delete_user(user.uid)
