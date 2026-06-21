import os
import json
import pytest
from cryptography.fernet import Fernet

os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())

from sidecar import storage

@pytest.fixture
def data_path(tmp_path, monkeypatch):
    path = str(tmp_path / "data.enc")
    monkeypatch.setattr(storage, "DATA_PATH", path)
    return path

def test_no_credentials_initially(data_path):
    assert storage.has_credentials() is False
    assert storage.load_credentials() is None

def test_save_and_load_credentials(data_path):
    storage.save_credentials("user@example.com", "secretpw")
    assert storage.has_credentials() is True
    creds = storage.load_credentials()
    assert creds == {"sr_email": "user@example.com", "sr_password": "secretpw"}

def test_save_and_load_voice_embedding(data_path):
    fake_embedding = b"\x01\x02\x03\x04"
    storage.save_voice_embedding(fake_embedding)
    assert storage.has_voice_embedding() is True
    assert storage.load_voice_embedding() == fake_embedding

def test_credentials_and_embedding_coexist(data_path):
    storage.save_credentials("a@b.com", "pw")
    storage.save_voice_embedding(b"\xff\xee")
    assert storage.load_credentials() == {"sr_email": "a@b.com", "sr_password": "pw"}
    assert storage.load_voice_embedding() == b"\xff\xee"
