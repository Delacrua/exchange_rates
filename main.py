from aiohttp import web
from aiohttp_pydantic import oas

from app.exchange_rates import routes as exchange_rate_routes


def setup_routes(application: web.Application) -> None:
    exchange_rate_routes.setup_routes(application)


def setup_app(application: web.Application):
    setup_routes(application)
    oas.setup(application, url_prefix="/docs")


def init_app(args=None) -> web.Application:
    application = web.Application()
    setup_app(application)
    return application


app = init_app(setup_app)
