from fastapi import FastAPI


def create_app():
    # pylint: disable=import-outside-toplevel
    new_app = FastAPI(title="YAACCU")

    from .views import router
    from yaaccu.db import db
    new_app.include_router(router)
    db.init_app(new_app)

    return new_app


app = create_app()
