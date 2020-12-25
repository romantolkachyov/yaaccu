from enum import Enum

from yaaccu.db import db


class AccountType(Enum):
    # the balance of the account should be greater than 0
    active = 'active'
    # the balance of the account should be less than 0
    passive = 'passive'
    # both positive and negative balance allowed
    normal = 'normal'


class Account(db.Model):
    __tablename__ = 'accounts'

    #: internal account id to build relations
    id = db.Column(db.BigInteger(), primary_key=True)
    #: account address: public key hash with `0x` prefix or custom name
    address = db.Column(db.Unicode(), unique=True, index=True)
    #: public key from the RSA key pair of the account owner
    pub_key = db.Column(db.Unicode(), unique=True, nullable=True, index=True)
    #: type of total balance restrictions applied to the account
    type = db.Column(db.Enum(AccountType), default=AccountType.active)
