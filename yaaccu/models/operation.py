from yaaccu.db import db


class Operation(db.Model):
    __tablename__ = 'operations'

    id = db.Column(db.BigInteger(), primary_key=True)
    document = db.Column(db.BigInteger(), db.ForeignKey('documents.id'))
    account = db.Column(db.BigInteger(), db.ForeignKey('accounts.id'))
    currency = db.Column(db.BigInteger(), db.ForeignKey('currencies.id'))
    amount = db.Column(db.Numeric(precision=16, scale=4))
