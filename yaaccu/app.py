import logging.config

from fastapi import FastAPI


def setup_logging():
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'class': 'logging.Formatter',
                'format': '%(asctime)s %(levelname)-7s %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': 'DEBUG',
            },
        },
        'loggers': {
            'yaaccu': {
                'handlers': ['console'],
                'level': 'DEBUG',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    })

setup_logging()


def create_app():
    app = FastAPI(title="YAACCU")

    # setup_logging()

    from .views import router
    from yaaccu.db import db
    app.include_router(router)
    db.init_app(app)

    # @app.on_event("startup")
    # async def startup_event():
    #     setup_logging()

    return app



