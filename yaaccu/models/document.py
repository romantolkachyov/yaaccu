import logging
from datetime import datetime
from decimal import Decimal

from gino.loader import ColumnLoader
from sqlalchemy import or_

from yaaccu.db import db

from .account import Account, AccountType
from .currency import Currency
from .operation import Operation

log = logging.getLogger('yaaccu')
log.disabled = property(lambda x: False)


class InvalidDocumentException(Exception):
    pass


class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.BigInteger(), primary_key=True)
    committed = db.Column(db.Boolean(), default=False)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)

    @classmethod
    async def create_transfer(cls,
                              sender: Account,
                              receiver: Account,
                              amount: Decimal,
                              currency: Currency):
        """Create transfer between two accounts.

        Create new document containing two operations: the first one subtract
        specified amount from the sender account and the other append the same
        amount to the account of the receiver.

        You must commit returned document manually.
        """
        async with db.transaction() as tx:
            doc = await cls.create()
            await Operation.create(
                document=doc.id,
                account=sender.id,
                currency=currency.id,
                amount=-amount
            )
            await Operation.create(
                document=doc.id,
                account=receiver.id,
                currency=currency.id,
                amount=amount
            )
            if not await doc.is_valid():
                tx.raise_rollback()
            return doc

    async def commit(self):
        """Commit document.

        Commit balance changes if current document is valid.

        Must be invoked outside transaction to ensure no conflicting document were added.
        """
        if await self.is_valid():
            await self.update(committed=True).apply()

    async def is_valid(self):
        """Check if document is valid.

        Checks if the total sum of the document operations is always zero per each used currency.
        Also, checks if each involved account will not become invalid after the document committed
        (like active account balance should be always positive and a passive account should be
        always negative or equal to zero).

        You must exit any transactions before invoking this method to be able to see operations
        created while your connection were isolated.

        Validation performed in two steps:

        1. at first time checks performed against all operations in the database (including
         not committed yet) to ensure we will not introduce conflicts with transactions prepared
         to commit: there is a possibility that other client performed his document validation before
         we inserted our one, so we should rollback it that case.

        2. the second time the same checks performed only on committed operations to ensure some
         uncommitted transactions from the first step didn't rolled back for some reason so we
         will not introduce inconsistency

        Other db clients follow the same rules so it is not possible to introduce conflicts between
        this checks (while our uncommitted document and operations is in the database).
        """
        # TODO: check if we are inside transaction and raise exception
        try:
            log.debug("Perform dirty document check")
            await self._per_currency_balance_is_valid()
            await self._per_account_balance_is_valid(include_dirty=True)

            log.debug("Perform clean document check")
            await self._per_account_balance_is_valid(include_dirty=False)
        except InvalidDocumentException as e:
            log.error("Document is not valid: %s", e.args[0])
            return False
        log.debug("Document is valid")
        return True

    async def _per_currency_balance_is_valid(self):
        # Check operation balance for each currency
        count_column = db.func.coalesce(db.func.sum(Operation.amount), 0)
        total_sum_qs = db.select([
            count_column,
            Currency.symbol
        ]).select_from(Operation.join(Currency)).where(Operation.document == self.id)

        total_sum_qs = total_sum_qs.group_by(Currency.symbol)

        balance_per_currency = await total_sum_qs.gino.load((
            ColumnLoader(count_column),
            ColumnLoader(Currency.symbol)
        )).all()
        log.debug("Balances per currency: %s", balance_per_currency)

        for balance, currency in balance_per_currency:
            if balance != 0:
                raise InvalidDocumentException(
                    "Document %s is invalid because has imbalance on currency %s" %
                    (self.id, currency)
                )

        return True

    async def _per_account_balance_is_valid(self, include_dirty=True):
        balance_column = db.func.coalesce(db.func.sum(Operation.amount), 0)
        # accounts_balances = db.select([
        #     balance_column,
        #     Account
        # ]).where(Operation.account == Account.id)

        accounts_balances = db.select([
            balance_column,
            Currency.symbol,
            Account
        ]).select_from(Operation.join(Account).join(Document).join(Currency)).where(Operation.account == Account.id)

        if not include_dirty:
            accounts_balances = accounts_balances.where(or_(Document.committed == True, Document.id == self.id))

        accounts_balances = accounts_balances.group_by(Account.id, Currency.symbol)

        balance_per_account = await accounts_balances.gino.load((
            ColumnLoader(balance_column),
            ColumnLoader(Currency.symbol),
            Account
        )).all()
        log.debug("Balances per account (with dirty operations): %s", balance_per_account)

        for balance, currency, account in balance_per_account:
            if account.type == AccountType.active and balance < 0:
                raise InvalidDocumentException(
                    "Active account %s balance will become less than zero which is invalid"
                    "(estimated balance: %s %s)" % (account.address, balance, currency)
                )
            if account.type == AccountType.passive and balance > 0:
                raise InvalidDocumentException(
                    "Passive account %s balance will become greater than zero which is invalid"
                    "(estimated balance: %s %s)" % (account.address, balance, currency)
                )

        return True
