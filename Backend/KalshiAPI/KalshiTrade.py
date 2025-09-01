from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from pathlib import Path
import time, uuid, base64, requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import padding

import requests
import datetime

#Load the private key stored in a file
def load_private_key_from_file(file_path):
    with open(file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,  # or provide a password if your key is encrypted
            backend=default_backend()
        )
    return private_key

#Sign text with private key
def sign_pss_text(private_key: rsa.RSAPrivateKey, text: str) -> str:
    message = text.encode('utf-8')
    try:
        signature = private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')
    except InvalidSignature as e:
        raise ValueError("RSA sign PSS failed") from e


#Send a request to Kalshi API with signed header
current_time = datetime.datetime.now()
timestamp = current_time.timestamp()
current_time_milliseconds = int(timestamp * 1000)
timestampt_str = str(current_time_milliseconds)

private_key = load_private_key_from_file('kalshi-key-2.key')

method = "GET"
base_url = 'https://demo-api.kalshi.co'
path='/trade-api/v2/portfolio/balance'

msg_string = timestampt_str + method + path
sig = sign_pss_text(private_key, msg_string)

headers = {
    'KALSHI-ACCESS-KEY': 'a952bcbe-ec3b-4b5b-b8f9-11dae589608c',
    'KALSHI-ACCESS-SIGNATURE': sig,
    'KALSHI-ACCESS-TIMESTAMP': timestampt_str
}

response = requests.get(base_url + path, headers=headers)

print(response.text)


# --- Config ---
BASE = "https://demo-api.kalshi.co"
PATH = "/trade-api/v2/portfolio/orders"
KEY_ID = "<YOUR_KEY_ID>"
KEY_PATH = Path("kalshi_private_key.pem")  # in .gitignore

#this is the basic structure for placing a trade
# # --- Load private key ---
# with open(KEY_PATH, "rb") as f:
#     private_key = serialization.load_pem_private_key(f.read(), password=None)
#
# def sign_message(msg: str) -> str:
#     sig = private_key.sign(
#         msg.encode(),
#         padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
#         hashes.SHA256(),
#     )
#     return base64.b64encode(sig).decode()
#
# # --- Prepare headers ---
# ts = str(int(time.time() * 1000))
# signature = sign_message(ts + "POST" + PATH)
#
# headers = {
#     "KALSHI-ACCESS-KEY": KEY_ID,
#     "KALSHI-ACCESS-TIMESTAMP": ts,
#     "KALSHI-ACCESS-SIGNATURE": signature,
#     "Content-Type": "application/json"
# }

#
# # --- Order payload ---
# order = {
#     "ticker": "US_PRES_2024",     # Example market ticker
#     "action": "buy",              # buy or sell
#     "side": "yes",                # yes or no
#     "count": 1,                   # # of contracts
#     "type": "limit",              # limit, market, etc.
#     "yes_price": 10,              # price in cents
#     "client_order_id": str(uuid.uuid4())
# }
#
# # --- Send POST ---
# resp = requests.post(BASE + PATH, headers=headers, json=order)
# print(resp.status_code)
# print(resp.json())