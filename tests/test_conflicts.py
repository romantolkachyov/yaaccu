from decimal import Decimal

import pytest


from yaaccu.models import (
    Document,
    AccountType, Operation,
)


@pytest.mark.asyncio
async def test_conflicting_documents_complex(create_account, currency):
    passive_acc = await create_account(AccountType.passive)
    acc1 = await create_account()
    acc2 = await create_account()
    acc3 = await create_account()

    # Fill acc1 with 1.00 (valid document)
    fill_doc = await Document.create_transfer(passive_acc, acc1, Decimal('1.00'), currency)

    # Create first valid document before committing fill_doc
    doc1 = await Document.create()
    await Operation.create(document=doc1.id, account=acc1.id, currency=currency.id, amount=Decimal('-1.00'))
    await Operation.create(document=doc1.id, account=acc2.id, currency=currency.id, amount=Decimal('1.00'))
    assert await doc1.is_valid() is False, "Should be invalid before fill committed"

    await fill_doc.commit()
    assert await doc1.is_valid() is True

    # The second document should be invalid in that case
    doc2 = await Document.create_transfer(acc1, acc3, Decimal('1.00'), currency)
    assert doc2 is None

    assert await doc1.is_valid() is True
    await doc1.commit()
