import logging
import time
from decimal import Decimal

from fastapi import Depends, APIRouter, HTTPException
from gino.exceptions import NoResultFound
from pydantic import BaseModel

from .db import db
from .security import get_current_account
from .models.account import Account
from .models.currency import Currency
from .models.document import Document
from .models.operation import Operation
from .utils import pub_key_to_account
from .signature import check_signature, InvalidSignature

router = APIRouter()


CREATE_ACCOUNT_TOKEN_EXPIRE_INTERVAL = 3600

log = logging.getLogger(__name__)


@router.get("/")
async def root():
    log.info("Hello world")
    return {"message": "Welcome to YAACCU!"}


@router.get('/balance')
async def account_balance(account=Depends(get_current_account)):
    balance = await db.select([
        db.func.coalesce(db.func.sum(Operation.amount), 0)
    ]).where(Operation.account == account.id).gino.scalar()
    return {
        "account": account.address,
        "balance": balance
    }


class CreateAccountRequest(BaseModel):
    """Request to create new account basing on signed public key.
    """
    #: signed public key
    pub_key: str
    #: sign timestamp (int only)
    timestamp: int
    #: public key signature: sign(pub_key + str(timestamp))
    sign: str


@router.post('/create/', status_code=201)
async def create_account(create_request: CreateAccountRequest):
    """Create new account using generate key pair.

    You should provide public key and signature proving your are the owner of the corresponding
    private key. `sign` must be a valid a PKCS#1 PSS signature for the provided public key.
    """
    try:
        if create_request.timestamp < time.time() - CREATE_ACCOUNT_TOKEN_EXPIRE_INTERVAL:
            raise InvalidSignature()
        content = ''.join([create_request.pub_key, str(create_request.timestamp)])
        check_signature(content, create_request.sign, create_request.pub_key)
    except InvalidSignature as e:
        raise HTTPException(status_code=400, detail="Invalid signature") from e

    account = await Account.create(
        address=pub_key_to_account(create_request.pub_key),
        pub_key=create_request.pub_key,
    )
    return {
        "account": account.address,
        "pub_key": account.pub_key
    }


class TransferInfo(BaseModel):
    receiver: str
    currency: str
    amount: Decimal


@router.post('/transfer/')
async def transfer(transfer_info: TransferInfo, account=Depends(get_current_account)):
    """Transfer funds from one account to another.
    """
    try:
        currency = await Currency.query.where(Currency.symbol == transfer_info.currency).gino.one()
    except NoResultFound as e:
        raise HTTPException(status_code=400, detail="Invalid currency") from e

    try:
        receiver = await Account.query.where(Account.address == transfer_info.receiver).gino.one()
    except NoResultFound as e:
        raise HTTPException(status_code=400, detail="Invalid receiver account") from e

    doc = await Document.create_transfer(
        sender=account,
        receiver=receiver,
        amount=transfer_info.amount,
        currency=currency
    )
    if doc:
        await doc.commit()
        return doc.to_dict()
    raise HTTPException(
        status_code=400,
        detail="Document is invalid. Try again later if you're pretty sure "
               "you meet all preconditions."
    )
