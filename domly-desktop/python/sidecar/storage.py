import os
import json
import base64
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# where the encrpyted file lives on disk
DATA_PATH = os.path.expanduser("~/.domly/data.enc")

# builds the cipher used to encprypt/ decrypt
def _get_fernet() -> Fernet:
    key = os.environ["ENCRYPTION_KEY"]
    return Fernet(key.encode())

# read and decrypts the whole file, returns it as a dict
def _read_data() -> dict:
    if not os.path.exists(DATA_PATH):
        return {} 
    with open(DATA_PATH, "rb") as f:
        encrypted = f.read()
    decrypted = _get_fernet().decrypt(encrypted)
    return json.loads(decrypted)

# Encrypts and writes the whole dict to disk, overwriting old contents
def _write_data(data: dict) -> None:
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    encrypted = _get_fernet().encrypt(json.dumps(data).encode())    
    with open(DATA_PATH, "wb") as f:
        f.write(encrypted)
    
# reads exisiting data first so we don't overwrite a saved voice embedding    
def save_credentials(sr_email: str, sr_password: str) -> None:
    data = _read_data()
    data["sr_email"] = sr_email    
    data["sr_password"] = sr_password    
    _write_data(data)
   
# returns the saved credentials, or None if nothing was saved yet    
def load_credentials() ->dict | None:
    data = _read_data()
    if "sr_email" not in data:
        return None
    return {"sr_email": data["sr_email"], "sr_password": data["sr_password"]}

def has_credentials() -> bool:
    return load_credentials() is not None

# JSON can't store raw binary, so we base64-encode it into test first
def save_voice_embedding(embeddings: bytes) -> None:
    data = _read_data()
    data["voice_embedding"] = base64.b64encode(embeddings).decode()
    _write_data(data)

def load_voice_embedding() -> bytes:
    data = _read_data()
    if "voice_embedding" not in data:
        return None
    return base64.b64decode(data["voice_embedding"])

def has_voice_embedding() -> bool:
    return load_voice_embedding() is not None
