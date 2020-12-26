from Cryptodome.Hash import SHA3_256
from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import pss


class InvalidSignature(Exception):
    pass


def check_signature(content: str, signature: str, pub_key: str, raise_exception=True):
    """Check signature on provided content using public key.

    :param content: signed content
    :param signature: signature
    :param pub_key: public key to check
    :param raise_exception: raise exception or just return False
    :return:
    """
    try:
        sign = bytes.fromhex(signature)
        verifier = pss.new(RSA.import_key(pub_key))
        # noinspection PyTypeChecker
        verifier.verify(SHA3_256.new(content.encode()), sign)  # type: ignore
    except (TypeError, ValueError) as e:
        if raise_exception:
            raise InvalidSignature() from e
        return False
    return True


def create_signature(content: str, private_key: str):
    cipher = pss.new(RSA.import_key(private_key))
    # noinspection PyTypeChecker
    return cipher.sign(SHA3_256.new(content.encode())).hex()  # type: ignore
