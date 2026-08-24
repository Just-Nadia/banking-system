"""
Кастомные исключения для банковской системы
"""

class AccountError(Exception):
    """Базовое исключение для всех ошибок счетов"""
    pass

class AccountFrozenError(AccountError):
    """Исключение при попытке операции с замороженным счётом"""
    def __init__(self, account_id: str, operation: str = "операция"):
        self.account_id = account_id
        self.operation = operation
        super().__init__(f"Счёт {account_id} заморожен. Невозможно выполнить: {operation}")

class AccountClosedError(AccountError):
    """Исключение при попытке операции с закрытым счётом"""
    def __init__(self, account_id: str, operation: str = "операция"):
        self.account_id = account_id
        self.operation = operation
        super().__init__(f"Счёт {account_id} закрыт. Невозможно выполнить: {operation}")

class InvalidOperationError(AccountError):
    """Исключение при некорректной операции"""
    def __init__(self, message: str):
        super().__init__(f"Некорректная операция: {message}")

class InsufficientFundsError(AccountError):
    """Исключение при недостатке средств"""
    def __init__(self, account_id: str, requested: float, available: float):
        self.account_id = account_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Недостаточно средств на счёте {account_id}. "
            f"Запрошено: {requested}, доступно: {available}"
        )