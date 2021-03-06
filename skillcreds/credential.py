"""
credential.py

module to help manage a credential JSON-LD document
"""
import base64
import datetime
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization as s11n
import json
from pyld import jsonld

# Credentials
def load_credential(filename):
  """Reads a credential document from filename and returns the compact
  JSON-LD representation of the credential."""
  with open(filename, 'r') as f:
    doc = json.load(f)
  return compact_credential(doc)


def compact_credential(doc):
  """Converts a JSON-LD credential into its compact representation."""
  context = doc.pop('@context', {})
  jsonld.set_document_loader(jsonld.requests_document_loader(timeout=5))
  credential = jsonld.compact(doc, context)
  return credential


## Issuer
def issuer_from_credential(credential):
  """Extracts the issuer from a credential."""
  return credential['ob:badge']['ocd:awardedBy']


def set_issuer_public_key(credential, issuer_public_key, issuer_key_id):
  issuer = issuer_from_credential(credential)
  issuer['ocd:publicKey'] = create_cryptographic_key(issuer_public_key,
                                                     issuer_key_id,
                                                     owner=issuer['@id'])


## Keys
def create_cryptographic_key(public_key, key_url, owner):
  """Create a LD CryptographicKey object from a RSA public key, with id=key_url, owner=owner."""
  public_key_bytes = public_key.public_bytes(encoding=s11n.Encoding.PEM,
                                             format=s11n.PublicFormat.SubjectPublicKeyInfo)
  return {
    "@id": key_url,
    "@type": "ob:CryptographicKey",
    "sec:owner": owner,
    "sec:publicKeyPem": public_key_bytes.decode('utf-8')
  }


def public_key_from_issuer(issuer):
  """Retrieves the public key from the credential and also converts to
  rsa_public_key. """
  public_key = issuer['ocd:publicKey']
  public_key_pem = public_key['sec:publicKeyPem']
  public_key_bytes = public_key_pem.encode('utf8')
  rsa_public_key = s11n.load_pem_public_key(public_key_bytes, default_backend())
  return public_key, rsa_public_key


def create_ld_signature(signature_bytes, creator, created, sig_type=None):
  """
  Parameters
    signautre: signature bytes object
  """
  if sig_type is None: sig_type = "ocd:RsaSignature2018"
  b64signature = base64.b64encode(signature_bytes)
  return {
    "@type": sig_type,
    "sec:creator": creator,
    "sec:created": created,
    "sec:signatureValue": b64signature.decode('utf-8')
  }


def signature_bytes_from_ld_signature(ld_signature):
  """
  Parameters:
    ld_signatue: LinkedDataSignatures object containing a signatureValue
                 key representing a base64 encoded signature of the
                 document
  """
  b64signature = ld_signature['sec:signatureValue'].encode('utf-8')
  return base64.b64decode(b64signature)
