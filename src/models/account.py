"""
Модели банковских счетов
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from enum import Enum

from .exceptions import (
    AccountFrozenError,
    AccountClosedError,
    InvalidOperationError,
    InsufficientFundsError
)


class AccountStatus(Enum):
    """Статусы счёта"""
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"

    def __str__(self):
        return self.value


class Currency(Enum):
    """Поддерживаемые валюты"""
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    KZT = "KZT"
    CNY = "CNY"

    def __str__(self):
        return self.value


class AbstractAccount(ABC):
    """
    Абстрактный базовый класс для всех банковских счетов
    """
    
    def __init__(
        self,
        owner: str,
        balance: float = 0.0,
        account_id: Optional[str] = None,
        currency: Currency = Currency.RUB
    ):
        self._account_id = account_id or self._generate_account_id()
        self._owner = owner
        self._balance = max(0.0, balance)
        self._status = AccountStatus.ACTIVE
        self._currency = currency
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self._transaction_history = []
    
    @staticmethod
    def _generate_account_id() -> str:
        """Генерация короткого UUID (8 символов)"""
        return str(uuid.uuid4())[:8].upper()
    
    @property
    def account_id(self) -> str:
        return self._account_id
    
    @property
    def owner(self) -> str:
        return self._owner
    
    @property
    def balance(self) -> float:
        return self._balance
    
    @property
    def status(self) -> AccountStatus:
        return self._status
    
    @property
    def currency(self) -> Currency:
        return self._currency
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def last_four_digits(self) -> str:
        return self._account_id[-4:] if len(self._account_id) >= 4 else self._account_id
    
    def _set_balance(self, new_balance: float) -> None:
        """Установка баланса (без проверки отрицательного значения)"""
        self._balance = new_balance
        self._updated_at = datetime.now()
    
    def _check_status(self) -> None:
        if self._status == AccountStatus.FROZEN:
            raise AccountFrozenError(self._account_id)
        if self._status == AccountStatus.CLOSED:
            raise AccountClosedError(self._account_id)
    
    def _validate_amount(self, amount: float) -> None:
        if not isinstance(amount, (int, float)):
            raise InvalidOperationError("Сумма должна быть числом")
        if amount <= 0:
            raise InvalidOperationError("Сумма должна быть положительной")
    
    def _ensure_sufficient_funds(self, amount: float) -> None:
        if amount > self._balance:
            raise InsufficientFundsError(self._account_id, amount, self._balance)
    
    @abstractmethod
    def deposit(self, amount: float) -> float:
        pass
    
    @abstractmethod
    def withdraw(self, amount: float) -> float:
        pass
    
    @abstractmethod
    def get_account_info(self) -> dict:
        pass
    
    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__} | "
            f"{self._owner} | "
            f"...{self.last_four_digits} | "
            f"{self._status} | "
            f"{self._balance:.2f} {self._currency.value}"
        )
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self._account_id}, owner={self._owner})>"


class BankAccount(AbstractAccount):
    """
    Конкретная реализация банковского счёта
    """
    
    def __init__(
        self,
        owner: str,
        balance: float = 0.0,
        account_id: Optional[str] = None,
        currency: Currency = Currency.RUB
    ):
        super().__init__(owner, balance, account_id, currency)
        self._transaction_history = []
    
    def deposit(self, amount: float) -> float:
        self._validate_amount(amount)
        self._check_status()
        
        new_balance = self._balance + amount
        self._set_balance(new_balance)
        
        self._transaction_history.append({
            'type': 'deposit',
            'amount': amount,
            'balance_after': new_balance,
            'timestamp': datetime.now()
        })
        
        return new_balance
    
    def withdraw(self, amount: float) -> float:
        self._validate_amount(amount)
        self._check_status()
        self._ensure_sufficient_funds(amount)
        
        new_balance = self._balance - amount
        if new_balance < 0:
            raise InvalidOperationError("Баланс не может быть отрицательным")
        self._set_balance(new_balance)
        
        self._transaction_history.append({
            'type': 'withdraw',
            'amount': amount,
            'balance_after': new_balance,
            'timestamp': datetime.now()
        })
        
        return new_balance
    
    def get_account_info(self) -> dict:
        return {
            'account_id': self._account_id,
            'owner': self._owner,
            'balance': self._balance,
            'currency': self._currency.value,
            'status': self._status.value,
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat(),
            'transactions_count': len(self._transaction_history),
            'type': self.__class__.__name__
        }
    
    def freeze(self) -> None:
        self._status = AccountStatus.FROZEN
        self._updated_at = datetime.now()
    
    def unfreeze(self) -> None:
        self._status = AccountStatus.ACTIVE
        self._updated_at = datetime.now()
    
    def close(self) -> None:
        if self._balance > 0:
            raise InvalidOperationError(
                f"Невозможно закрыть счёт с положительным балансом: {self._balance}"
            )
        self._status = AccountStatus.CLOSED
        self._updated_at = datetime.now()
    
    def get_transaction_history(self) -> list:
        return self._transaction_history.copy()


class SavingsAccount(BankAccount):
    """
    Сберегательный счёт с минимальным остатком и процентами
    """
    
    def __init__(
        self,
        owner: str,
        balance: float = 0.0,
        account_id: Optional[str] = None,
        currency: Currency = Currency.RUB,
        min_balance: float = 100.0,
        monthly_interest_rate: float = 0.05
    ):
        super().__init__(owner, balance, account_id, currency)
        self._min_balance = min_balance
        self._monthly_interest_rate = monthly_interest_rate
    
    @property
    def min_balance(self) -> float:
        return self._min_balance
    
    @property
    def monthly_interest_rate(self) -> float:
        return self._monthly_interest_rate
    
    def withdraw(self, amount: float) -> float:
        """Снятие с проверкой минимального остатка"""
        self._validate_amount(amount)
        self._check_status()
        
        if self._balance - amount < self._min_balance:
            raise InvalidOperationError(
                f"Нельзя снять {amount}. Минимальный остаток должен быть {self._min_balance}"
            )
        
        self._ensure_sufficient_funds(amount)
        
        new_balance = self._balance - amount
        if new_balance < 0:
            raise InvalidOperationError("Баланс не может быть отрицательным")
        self._set_balance(new_balance)
        
        self._transaction_history.append({
            'type': 'withdraw',
            'amount': amount,
            'balance_after': new_balance,
            'timestamp': datetime.now()
        })
        
        return new_balance
    
    def apply_monthly_interest(self) -> float:
        """Начисление процентов за месяц"""
        self._check_status()
        
        interest = self._balance * (self._monthly_interest_rate / 12)
        self._balance += interest
        self._updated_at = datetime.now()
        
        self._transaction_history.append({
            'type': 'interest',
            'amount': interest,
            'balance_after': self._balance,
            'timestamp': datetime.now()
        })
        
        return interest
    
    def get_account_info(self) -> dict:
        info = super().get_account_info()
        info['min_balance'] = self._min_balance
        info['monthly_interest_rate'] = self._monthly_interest_rate
        info['type'] = self.__class__.__name__
        return info
    
    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__} | "
            f"{self._owner} | "
            f"...{self.last_four_digits} | "
            f"{self._status} | "
            f"{self._balance:.2f} {self._currency.value} | "
            f"{self._monthly_interest_rate*100:.1f}%"
        )


class PremiumAccount(BankAccount):
    """
    Премиум-счёт с овердрафтом и комиссией
    """
    
    def __init__(
        self,
        owner: str,
        balance: float = 0.0,
        account_id: Optional[str] = None,
        currency: Currency = Currency.RUB,
        overdraft_limit: float = 10000.0,
        monthly_fee: float = 500.0
    ):
        super().__init__(owner, balance, account_id, currency)
        self._overdraft_limit = overdraft_limit
        self._monthly_fee = monthly_fee
    
    @property
    def overdraft_limit(self) -> float:
        return self._overdraft_limit
    
    @property
    def monthly_fee(self) -> float:
        return self._monthly_fee
    
    def withdraw(self, amount: float) -> float:
        """Снятие с возможностью овердрафта"""
        self._validate_amount(amount)
        self._check_status()
        
        available = self._balance + self._overdraft_limit
        if amount > available:
            raise InsufficientFundsError(
                self._account_id, 
                amount, 
                available
            )
        
        new_balance = self._balance - amount
        # Овердрафт разрешён — проверка отрицательного баланса не нужна
        self._set_balance(new_balance)
        
        self._transaction_history.append({
            'type': 'withdraw',
            'amount': amount,
            'balance_after': new_balance,
            'timestamp': datetime.now()
        })
        
        return new_balance
    
    def apply_monthly_fee(self) -> float:
        """Списание ежемесячной комиссии"""
        self._check_status()
        
        available = self._balance + self._overdraft_limit
        if self._monthly_fee > available:
            raise InsufficientFundsError(
                self._account_id,
                self._monthly_fee,
                available
            )
        
        self._balance -= self._monthly_fee
        self._updated_at = datetime.now()
        
        self._transaction_history.append({
            'type': 'fee',
            'amount': self._monthly_fee,
            'balance_after': self._balance,
            'timestamp': datetime.now()
        })
        
        return self._monthly_fee
    
    def get_account_info(self) -> dict:
        info = super().get_account_info()
        info['overdraft_limit'] = self._overdraft_limit
        info['monthly_fee'] = self._monthly_fee
        info['available_funds'] = self._balance + self._overdraft_limit
        info['type'] = self.__class__.__name__
        return info
    
    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__} | "
            f"{self._owner} | "
            f"...{self.last_four_digits} | "
            f"{self._status} | "
            f"{self._balance:.2f} {self._currency.value} | "
            f"овердрафт: {self._overdraft_limit}"
        )


class InvestmentAccount(BankAccount):
    """
    Инвестиционный счёт с портфелем активов
    """
    
    def __init__(
        self,
        owner: str,
        balance: float = 0.0,
        account_id: Optional[str] = None,
        currency: Currency = Currency.RUB,
        stocks: list = None,
        bonds: list = None,
        etf: list = None
    ):
        super().__init__(owner, balance, account_id, currency)
        self._stocks = stocks or []
        self._bonds = bonds or []
        self._etf = etf or []
        self._portfolio_value = 0.0
        self._update_portfolio_value()
    
    @property
    def stocks(self) -> list:
        return self._stocks.copy()
    
    @property
    def bonds(self) -> list:
        return self._bonds.copy()
    
    @property
    def etf(self) -> list:
        return self._etf.copy()
    
    @property
    def portfolio_value(self) -> float:
        self._update_portfolio_value()
        return self._portfolio_value
    
    def _update_portfolio_value(self) -> None:
        self._portfolio_value = (
            sum(self._stocks) + sum(self._bonds) + sum(self._etf)
        )
    
    def add_stock(self, value: float) -> None:
        self._validate_amount(value)
        self._stocks.append(value)
        self._update_portfolio_value()
        self._updated_at = datetime.now()
    
    def add_bond(self, value: float) -> None:
        self._validate_amount(value)
        self._bonds.append(value)
        self._update_portfolio_value()
        self._updated_at = datetime.now()
    
    def add_etf(self, value: float) -> None:
        self._validate_amount(value)
        self._etf.append(value)
        self._update_portfolio_value()
        self._updated_at = datetime.now()
    
    def project_yearly_growth(self, rate: float = 0.12) -> float:
        return self._portfolio_value * rate
    
    def get_account_info(self) -> dict:
        info = super().get_account_info()
        info['stocks_count'] = len(self._stocks)
        info['bonds_count'] = len(self._bonds)
        info['etf_count'] = len(self._etf)
        info['portfolio_value'] = self._portfolio_value
        info['type'] = self.__class__.__name__
        return info
    
    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__} | "
            f"{self._owner} | "
            f"...{self.last_four_digits} | "
            f"{self._status} | "
            f"{self._balance:.2f} {self._currency.value} | "
            f"портфель: {self._portfolio_value:.2f}"
        )