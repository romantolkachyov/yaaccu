from sqlalchemy.engine.url import URL, make_url
from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")

TESTING = config("TESTING", cast=bool, default=False)

DB_DRIVER = config("DB_DRIVER", default="postgresql")
DB_HOST = config("DB_HOST", default=None)
DB_PORT = config("DB_PORT", cast=int, default=None)
DB_USER = config("DB_USER", default=None)
DB_PASSWORD = config("DB_PASSWORD", cast=Secret, default=None)
DB_DATABASE = config("DB_DATABASE", default=None)
if TESTING:
    if DB_DATABASE:  # pragma: no cover
        DB_DATABASE += "_test"
    else:
        DB_DATABASE = "yaaccu_test"
DB_DSN = config(
    "DB_DSN",
    cast=make_url,
    default=URL(
        drivername=DB_DRIVER,
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_DATABASE,
    ),
)
DB_POOL_MIN_SIZE = config("DB_POOL_MIN_SIZE", cast=int, default=1)
DB_POOL_MAX_SIZE = config("DB_POOL_MAX_SIZE", cast=int, default=16)
DB_ECHO = config("DB_ECHO", cast=bool, default=False)
DB_SSL = config("DB_SSL", default=None)
DB_USE_CONNECTION_FOR_REQUEST = config(
    "DB_USE_CONNECTION_FOR_REQUEST", cast=bool, default=True
)
DB_RETRY_LIMIT = config("DB_RETRY_LIMIT", cast=int, default=1)
DB_RETRY_INTERVAL = config("DB_RETRY_INTERVAL", cast=int, default=1)

# Test database

TEST_DB_DRIVER = config("TEST_DB_DRIVER", default=DB_DRIVER)
TEST_DB_HOST = config("TEST_DB_HOST", default=None)
TEST_DB_PORT = config("TEST_DB_PORT", cast=int, default=DB_PORT)
TEST_DB_USER = config("TEST_DB_USER", default=DB_USER)
TEST_DB_PASSWORD = config("TEST_DB_PASSWORD", cast=Secret, default=DB_PASSWORD)
TEST_DB_DATABASE = config("TEST_DB_DATABASE", default=DB_DATABASE)
