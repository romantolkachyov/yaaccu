import asyncio
import time
from functools import wraps

import pytest
from Cryptodome.PublicKey import RSA
from Cryptodome.Hash import SHA3_256
from Cryptodome.Signature import pss

from yaaccu.models import Account, AccountType
from yaaccu.utils import create_token, pub_key_to_account

test_deposit_key = RSA.generate(1024)
test_key = RSA.generate(1024)
test_key2 = RSA.generate(1024)


@pytest.fixture()
def create_account(client):
    @wraps(create_account)
    async def _factory(key, t=None):
        timestamp = t if t is not None else int(time.time())
        pub_key = key.publickey().export_key().decode()
        # noinspection PyTypeChecker
        sign = pss.new(key).sign(
            SHA3_256.new(''.join([
                pub_key,
                str(timestamp)
            ]).encode())
        ).hex()
        response = await client.post('/create/', json={
            "pub_key": pub_key,
            "timestamp": timestamp,
            "sign": sign
        })
        assert response.status_code == 201, "Wrong create account status %s" % response.content
        d = response.json()
        assert 'account' in d
        assert 'pub_key' in d
        return d['account']
    return _factory


@pytest.fixture()
def make_transfer(client):
    @wraps(make_transfer)
    async def _make_transfer(sender_key, to_account, amount, currency, ignore_failed=False):
        response = await client.post("/transfer/", json={
            'receiver': to_account,
            'currency': currency.symbol,
            'amount': amount
        }, headers={
            'X-Token': create_token(sender_key).decode()
        })
        if not ignore_failed:
            assert response.status_code == 200, "Invalid status code %s" % response.content
        return response
    return _make_transfer


@pytest.mark.asyncio
async def test_home(client):
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_balance(client, create_account, make_transfer, currency):
    acc1 = await create_account(test_key)

    # check initial account balance
    response = await client.get('/balance', headers={
        'X-Token': create_token(test_key).decode()
    })
    assert response.status_code == 200
    assert response.json()['balance'] == 0

    # fill acc1
    await Account.create(
        address='deposit',
        pub_key=test_deposit_key.publickey().export_key().decode(),
        type=AccountType.passive
    )
    response = await make_transfer(test_deposit_key, acc1, '1.00', currency)
    assert response.status_code == 200

    # check balance changed after filled
    response = await client.get('/balance', headers={
        'X-Token': create_token(test_key).decode()
    })
    assert response.status_code == 200
    assert response.json()['balance'] == 1


@pytest.mark.asyncio
async def test_unregistered_pub_key(client, currency, create_account):
    acc2 = await create_account(test_key2)

    response = await client.post("/transfer/", json={
        'receiver': acc2,
        'currency': currency.symbol,
        'amount': '1.00'
    }, headers={
        'X-Token': create_token(test_key).decode()
    })
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_send_to_unregistered_pub_key(client, currency, create_account):
    await create_account(test_key)

    response = await client.post("/transfer/", json={
        'receiver': pub_key_to_account(test_key2.publickey().export_key()),
        'currency': currency.symbol,
        'amount': '1.00'
    }, headers={
        'X-Token': create_token(test_key).decode()
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_account(create_account):
    assert await create_account(test_key)


@pytest.mark.asyncio
async def test_create_account_invalid_sign(create_account):
    with pytest.raises(AssertionError):
        await create_account(test_key, t=0)  # expired timestamp


@pytest.mark.asyncio
async def test_invalid_token(client, create_account, currency):
    await create_account(test_key)
    acc2 = await create_account(test_key2)

    response = await client.post("/transfer/", json={
        'receiver': acc2,
        'currency': currency.symbol,
        'amount': '1.00'
    }, headers={
        'X-Token': 'INVALID'
    })
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_expired_token(client, create_account, currency):
    acc1 = await create_account(test_key)
    await create_account(test_key2)

    response = await client.post("/transfer/", json={
        'receiver': acc1,
        'currency': currency.symbol,
        'amount': '1.00'
    }, headers={
        'X-Token': create_token(test_key2, t=1).decode()
    })
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_invalid_token_sign(client, create_account, currency):
    acc1 = await create_account(test_key)
    await create_account(test_key2)

    response = await client.post("/transfer/", json={
        'receiver': acc1,
        'currency': currency.symbol,
        'amount': '1.00'
    }, headers={
        'X-Token': create_token(test_key2, signature='123').decode()
    })
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_transfer_invalid_currency(client, create_account):
    await create_account(test_key)
    to_account = await create_account(test_key2)
    response = await client.post("/transfer/", json={
        'receiver': to_account,
        'currency': 'INVALID',
        'amount': '1.00'
    }, headers={
        'X-Token': create_token(test_key).decode()
    })
    assert response.status_code == 400, "Should fail with invalid currency: %s" % response.content
    return response


@pytest.mark.asyncio
async def test_success_transfer(make_transfer, create_account, currency):
    """Test success transfer.

    Create three accounts: deposit, acc1, acc2.
    Charge acc1 from deposit, transfer from acc1 to acc2.
    """
    acc1 = await create_account(test_key)
    acc2 = await create_account(test_key2)

    await Account.create(
        address='deposit',
        pub_key=test_deposit_key.publickey().export_key().decode(),
        type=AccountType.passive
    )

    response = await make_transfer(test_deposit_key, acc1, '1.00', currency)
    assert response.status_code == 200, \
        "Invalid status code while trying to charge from deposit account %s" % response.content

    response = await make_transfer(test_key, acc2, '1.00', currency)
    assert response.status_code == 200, "Invalid status code %s" % response.content


@pytest.mark.asyncio
async def test_race_condition(make_transfer, create_account, currency, client):
    # create account
    # fill account
    # create N tasks and start them in parallel
    # TODO: check if last view line covered
    acc1 = await create_account(test_key)
    acc2 = await create_account(test_key2)

    await Account.create(
        address='deposit',
        pub_key=test_deposit_key.publickey().export_key().decode(),
        type=AccountType.passive
    )

    await make_transfer(test_deposit_key, acc1, '1.00', currency)

    await asyncio.gather(*[
        make_transfer(test_key, acc2, '1.00', currency, ignore_failed=True) for _ in range(10)
    ])

    response = await client.get('/balance', headers={
        'X-Token': create_token(test_key).decode()
    })
    assert response.status_code == 200, "Wrong status %s" % response.content
    assert response.json()['balance'] == 0

    response = await client.get('/balance', headers={
        'X-Token': create_token(test_key2).decode()
    })
    assert response.status_code == 200, "Wrong status %s" % response.content
    assert response.json()['balance'] == 1


@pytest.mark.asyncio
async def test_transfer_insufficient_funds(create_account, currency, make_transfer):
    await create_account(test_key)
    acc = await create_account(test_key2)

    with pytest.raises(AssertionError):
        await make_transfer(test_key, acc, '1.00', currency)
