import time
import logging
from base64 import b64decode

import orjson
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from yaaccu.models.account import Account
from yaaccu.signature import check_signature, InvalidSignature

token_header = APIKeyHeader(name='X-Token')

TOKEN_EXPIRE_INTERVAL = 3600


def decode_token(token: str):
    """Decode base64 token containing json-serialized value.

    Check sign, token expiration time and return encoded public key.
    """
    decoded = b64decode(token.encode())

    try:
        key_data = orjson.loads(decoded)
        timestamp = int(key_data['t'])
        pub_key = key_data['p']
        signature = key_data['s']
    except (ValueError, TypeError, KeyError, orjson.JSONDecodeError) as e:
        logging.debug("Invalid token format: %s", decoded)
        raise HTTPException(status_code=403, detail="Invalid token") from e

    if timestamp > time.time() or timestamp < time.time() - TOKEN_EXPIRE_INTERVAL:
        raise HTTPException(status_code=403, detail="Token expired")

    try:
        check_signature(
            ''.join([pub_key, str(timestamp)]),
            signature,
            pub_key
        )
    except InvalidSignature:
        logging.error("Invalid token signature. Might be access violation.")
        raise HTTPException(status_code=403, detail="Invalid token")

    return pub_key


def get_current_pub_key(token: str = Depends(token_header)):
    """Get public key of the current client from the token.
    """
    return decode_token(token)


async def get_current_account(pub_key: str = Depends(get_current_pub_key)):
    """Get current Account or return 403 response.
    """
    account = await Account.query.where(Account.pub_key == pub_key).gino.first()
    if account is None:
        raise HTTPException(status_code=403, detail="Account doesn't exist")
    return account
