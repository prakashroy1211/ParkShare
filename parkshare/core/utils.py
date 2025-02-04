from django.core.signing import Signer
from django.conf import settings

signer = Signer(salt=settings.SECRET_KEY)

def generate_verification_token(email):
    return signer.sign(email)

def verify_token(token):
    try:
        return signer.unsign(token)
    except:
        return None
