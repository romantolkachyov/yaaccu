from yaaccu.db import db


class Currency(db.Model):
    __tablename__ = 'currencies'

    id = db.Column(db.BigInteger(), primary_key=True)
    name = db.Column(db.Unicode(), unique=True)
    symbol = db.Column(db.Unicode(), unique=True, index=True)
