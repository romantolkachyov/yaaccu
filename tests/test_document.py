import pytest

from yaaccu.models import (
    AccountType,
    Operation,
    Document,
)


@pytest.fixture
async def passive_acc(create_account):
    return await create_account(AccountType.passive)


@pytest.fixture
async def active_acc(create_account):
    return await create_account(AccountType.active)


@pytest.mark.asyncio
async def test_simple_valid_document(passive_acc, active_acc, currency):
    """Transfer 1.00 amount from one account to another.
    """
    doc = await Document.create()
    assert await doc.is_valid()

    await Operation.create(document=doc.id, account=passive_acc.id, currency=currency.id, amount='-1.00')
    await Operation.create(document=doc.id, account=active_acc.id, currency=currency.id, amount='1.00')
    assert await doc.is_valid() is True


@pytest.mark.asyncio
async def test_two_currency_valid_document(active_acc, passive_acc, currency, currency2):
    doc = await Document.create()
    assert await doc.is_valid()

    await Operation.create(document=doc.id, account=passive_acc.id, currency=currency.id, amount='-1.00')
    await Operation.create(document=doc.id, account=active_acc.id, currency=currency.id, amount='1.00')
    await Operation.create(document=doc.id, account=passive_acc.id, currency=currency2.id, amount='-1.00')
    await Operation.create(document=doc.id, account=active_acc.id, currency=currency2.id, amount='1.00')
    assert await doc.is_valid() is True


@pytest.mark.asyncio
async def test_single_operation_imbalance(passive_acc, currency):
    doc = await Document.create()

    await Operation.create(document=doc.id, account=passive_acc.id, currency=currency.id, amount='1.00')
    assert await doc.is_valid() is False, "Document should be imbalanced because has only one operation"


@pytest.mark.asyncio
async def test_two_currency_imbalance(passive_acc, active_acc, currency, currency2):
    """Test imbalance of the document with two operations in two different currencies.
    """
    doc = await Document.create()

    await Operation.create(document=doc.id, account=passive_acc.id, currency=currency.id, amount='-1.00')
    await Operation.create(document=doc.id, account=active_acc.id, currency=currency2.id, amount='1.00')
    assert await doc.is_valid() is False, "Document should be imbalanced because there are two operations" \
                                          "with different currencies (but the total sum is 0 which may be a problem)"


@pytest.mark.asyncio
async def test_active_account_negative_balance(create_account, active_acc, currency):
    doc = await Document.create()

    active_acc2 = await create_account(AccountType.active)
    await Operation.create(document=doc.id, account=active_acc.id, currency=currency.id, amount='1.00')
    await Operation.create(document=doc.id, account=active_acc2.id, currency=currency.id, amount='-1.00')
    assert await doc.is_valid() is False


@pytest.mark.asyncio
async def test_passive_account_negative_balance(create_account, passive_acc, currency):
    doc = await Document.create()

    passive_acc2 = await create_account(AccountType.passive)
    await Operation.create(document=doc.id, account=passive_acc.id, currency=currency.id, amount='1.00')
    await Operation.create(document=doc.id, account=passive_acc2.id, currency=currency.id, amount='-1.00')
    assert await doc.is_valid() is False
