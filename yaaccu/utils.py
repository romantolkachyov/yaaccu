import time
from base64 import b64encode
from typing import Union

import orjson
from Cryptodome.Hash import SHA3_256
from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import pss


KEY_SIZE = 1024


def create_token(key=None):
    if key is None:
        key = RSA.generate(KEY_SIZE)
    d = {
        't': int(time.time()),
        'p': key.publickey().export_key().decode()
    }
    sign_content = (''.join([d['p'], str(d['t'])])).encode()
    d['s'] = pss.new(key).sign(SHA3_256.new(sign_content)).hex()
    return b64encode(orjson.dumps(d))


def pub_key_to_account(pub_key: Union[str, bytes]):
    if isinstance(pub_key, str):
        pub_key = pub_key.encode()
    return '0x' + SHA3_256.new(pub_key).hexdigest()
