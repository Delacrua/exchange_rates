from app.exchange_rates import views


def setup_routes(app):
    app.router.add_view("/api/v1/convert", views.ExchangeRatesView)
