"""SHA-256 identity for maintained build and validation artifacts."""
import hashlib


def digest(data):
    return hashlib.sha256(data).hexdigest()
