import os
from dataclasses import dataclass
from typing import Tuple, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


@dataclass
class RSAKeyPair:
    private_key: rsa.RSAPrivateKey
    public_key: rsa.RSAPublicKey


def generate_rsa_keypair(bits: int = 2048) -> RSAKeyPair:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    return RSAKeyPair(private_key=private_key, public_key=private_key.public_key())


def rsa_encrypt(public_key: rsa.RSAPublicKey, plaintext: bytes) -> bytes:
    return public_key.encrypt(
        plaintext,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )


def rsa_decrypt(private_key: rsa.RSAPrivateKey, ciphertext: bytes) -> bytes:
    return private_key.decrypt(
        ciphertext,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )


@dataclass
class ECCKeyPair:
    private_key: ec.EllipticCurvePrivateKey
    public_key: ec.EllipticCurvePublicKey


def generate_ecc_keypair(curve: ec.EllipticCurve = ec.SECP256R1()) -> ECCKeyPair:
    private_key = ec.generate_private_key(curve)
    return ECCKeyPair(private_key=private_key, public_key=private_key.public_key())


def aes_gcm_encrypt(key: bytes, plaintext: bytes, associated_data: Optional[bytes] = None) -> Tuple[bytes, bytes, bytes]:
    iv = os.urandom(12)
    encryptor = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend()).encryptor()
    if associated_data:
        encryptor.authenticate_additional_data(associated_data)
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return iv, ciphertext, encryptor.tag


def aes_gcm_decrypt(key: bytes, iv: bytes, ciphertext: bytes, tag: bytes, associated_data: Optional[bytes] = None) -> bytes:
    decryptor = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend()).decryptor()
    if associated_data:
        decryptor.authenticate_additional_data(associated_data)
    return decryptor.update(ciphertext) + decryptor.finalize()
