import logging
from functools import wraps

import pytest
from Cryptodome.PublicKey import RSA
from alembic.config import main
from starlette.config import environ
from async_asgi_testclient import TestClient

environ["TESTING"] = "TRUE"
environ["DB_HOST"] = environ["TEST_DB_HOST"]
# TODO: allow other options to override


@pytest.fixture(autouse=True)
def app():
    from yaaccu.app import create_app

    app = create_app()

    main(["--raiseerr", "upgrade", "head"])

    yield app

    main(["--raiseerr", "downgrade", "base"])


@pytest.fixture
async def client(app):
    async with TestClient(app) as client:
        logging.getLogger('yaaccu').disabled = False
        yield client


@pytest.fixture
async def currency(client):
    from yaaccu.models.currency import Currency

    return await Currency.create(name='US Dollar', symbol='USD')


@pytest.fixture
async def currency2(client):
    from yaaccu.models.currency import Currency

    return await Currency.create(name='Euro', symbol='EUR')


@pytest.fixture
def create_account(client):
    """Test fixture containing test Account factory function.
    """
    from yaaccu.models import AccountType, Account
    from yaaccu.utils import pub_key_to_account

    @wraps(create_account)
    async def _inner(type: AccountType = AccountType.active):
        pub_key = RSA.generate(1024).publickey().export_key().decode()
        return await Account.create(
            address=pub_key_to_account(pub_key),
            pub_key=pub_key,
            type=type,
        )
    return _inner
