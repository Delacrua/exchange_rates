class ManagerException(Exception):
    pass


class ExchangeRequestException(ManagerException):
    pass


class PairNotFoundException(ManagerException):
    pass


class ExchangeRatesServiceException(Exception):
    pass
