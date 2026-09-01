"""
Обработчик транзакций
"""

from datetime import datetime
from typing import Optional, List, Dict

from .account import AbstractAccount, PremiumAccount, Currency
from .transaction import (
    Transaction,
    TransactionQueue,
    TransactionType,
    TransactionPriority
)
from .exceptions import (
    InvalidOperationError,
    InsufficientFundsError
)


class TransactionProcessor:
    """
    Обработчик транзакций
    """
    
    COMMISSION_RATES = {
        TransactionType.TRANSFER: 0.01,
        TransactionType.EXTERNAL: 0.03,
        TransactionType.WITHDRAW: 0.005,
        TransactionType.DEPOSIT: 0.0,
        TransactionType.INTERNAL: 0.0,
    }
    
    EXCHANGE_RATES = {
        ('RUB', 'USD'): 0.011,
        ('RUB', 'EUR'): 0.010,
        ('USD', 'RUB'): 90.0,
        ('EUR', 'RUB'): 100.0,
        ('USD', 'EUR'): 0.92,
        ('EUR', 'USD'): 1.09,
    }
    
    def __init__(self, risk_analyzer=None):
        self._queue = TransactionQueue()
        self._processed: List[Transaction] = []
        self._errors: List[str] = []
        self._risk_analyzer = risk_analyzer
    
    @property
    def queue(self) -> TransactionQueue:
        return self._queue
    
    @property
    def processed_count(self) -> int:
        return len(self._processed)
    
    def add_transaction(
        self,
        transaction: Transaction,
        priority: TransactionPriority = TransactionPriority.NORMAL,
        delay_seconds: int = 0
    ) -> None:
        if delay_seconds > 0:
            self._queue.add_delayed(transaction, delay_seconds)
        else:
            self._queue.add_priority(transaction, priority)
    
    def _calculate_commission(self, transaction: Transaction, account: Optional[AbstractAccount] = None) -> float:
        if account and isinstance(account, PremiumAccount):
            return 0.0
        
        rate = self.COMMISSION_RATES.get(transaction.transaction_type, 0.01)
        
        if transaction.is_external:
            rate = max(rate, 0.03)
        
        return transaction.amount * rate
    
    def _convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        if from_currency == to_currency:
            return amount
        
        key = (from_currency, to_currency)
        rate = self.EXCHANGE_RATES.get(key)
        
        if rate is None:
            reverse_key = (to_currency, from_currency)
            reverse_rate = self.EXCHANGE_RATES.get(reverse_key)
            if reverse_rate:
                return amount / reverse_rate
            raise ValueError(f"Курс {from_currency}->{to_currency} не найден")
        
        return amount * rate
    
    def _get_account(self, account_id: str, accounts: Dict[str, AbstractAccount]) -> Optional[AbstractAccount]:
        return accounts.get(account_id)
    
    def process_next(self, accounts: Dict[str, AbstractAccount]) -> Optional[Transaction]:
        # Проверяем отложенные транзакции
        self._queue.check_delayed()
        
        transaction = self._queue.get_next()
        if not transaction:
            return None
        
        # Проверка риска
        if self._risk_analyzer:
            blocked, reasons = self._risk_analyzer.is_operation_blocked(transaction, accounts)
            if blocked:
                error_msg = f"Транзакция заблокирована: {', '.join(reasons)}"
                self._errors.append(error_msg)
                self._queue.fail(transaction, error_msg)
                return transaction
        
        try:
            self._process_transaction(transaction, accounts)
            self._queue.complete(transaction)
            self._processed.append(transaction)
            return transaction
            
        except Exception as e:
            error_msg = f"Ошибка транзакции {transaction.transaction_id}: {str(e)}"
            self._errors.append(error_msg)
            
            if transaction.can_retry():
                transaction.increment_retry()
                self._queue.add(transaction)
            else:
                self._queue.fail(transaction, str(e))
            
            return transaction
    
    def _process_transaction(self, transaction: Transaction, accounts: Dict[str, AbstractAccount]) -> None:
        current_hour = datetime.now().hour
        if 0 <= current_hour < 5:
            raise InvalidOperationError("Транзакции запрещены с 00:00 до 05:00")
        
        if transaction.transaction_type == TransactionType.DEPOSIT:
            self._process_deposit(transaction, accounts)
        elif transaction.transaction_type == TransactionType.WITHDRAW:
            self._process_withdraw(transaction, accounts)
        elif transaction.transaction_type in [TransactionType.TRANSFER, TransactionType.INTERNAL, TransactionType.EXTERNAL]:
            self._process_transfer(transaction, accounts)
        else:
            raise InvalidOperationError(f"Неизвестный тип транзакции: {transaction.transaction_type}")
    
    def _process_deposit(self, transaction: Transaction, accounts: Dict[str, AbstractAccount]) -> None:
        if not transaction.receiver:
            raise InvalidOperationError("Не указан получатель для пополнения")
        
        account = self._get_account(transaction.receiver, accounts)
        if not account:
            raise ValueError(f"Счёт {transaction.receiver} не найден")
        
        amount = self._convert_currency(transaction.amount, transaction.currency, account.currency.value)
        account.deposit(amount)
    
    def _process_withdraw(self, transaction: Transaction, accounts: Dict[str, AbstractAccount]) -> None:
        if not transaction.sender:
            raise InvalidOperationError("Не указан отправитель для снятия")
        
        account = self._get_account(transaction.sender, accounts)
        if not account:
            raise ValueError(f"Счёт {transaction.sender} не найден")
        
        account._check_status()
        
        amount = self._convert_currency(transaction.amount, transaction.currency, account.currency.value)
        commission = self._calculate_commission(transaction, account)
        commission_converted = self._convert_currency(commission, transaction.currency, account.currency.value)
        total = amount + commission_converted
        
        account.withdraw(total)
    
    def _process_transfer(self, transaction: Transaction, accounts: Dict[str, AbstractAccount]) -> None:
        if not transaction.sender:
            raise InvalidOperationError("Не указан отправитель")
        if not transaction.receiver:
            raise InvalidOperationError("Не указан получатель")
        
        sender = self._get_account(transaction.sender, accounts)
        receiver = self._get_account(transaction.receiver, accounts)
        
        if not sender:
            raise ValueError(f"Счёт отправителя {transaction.sender} не найден")
        if not receiver:
            raise ValueError(f"Счёт получателя {transaction.receiver} не найден")
        
        # Проверка статуса отправителя
        sender._check_status()
        
        # Проверка статуса получателя
        receiver._check_status()
        
        # Конвертация суммы
        amount = self._convert_currency(transaction.amount, transaction.currency, sender.currency.value)
        commission = self._calculate_commission(transaction, sender)
        commission_converted = self._convert_currency(commission, transaction.currency, sender.currency.value)
        total = amount + commission_converted
        
        # Проверка достаточности средств
        if not isinstance(sender, PremiumAccount):
            if total > sender.balance:
                raise InsufficientFundsError(sender.account_id, total, sender.balance)
        
        # Все проверки пройдены → списываем
        sender.withdraw(total)
        
        # Конвертируем для получателя
        amount_receiver = self._convert_currency(transaction.amount, transaction.currency, receiver.currency.value)
        
        # Зачисляем получателю
        receiver.deposit(amount_receiver)
    
    def process_all(self, accounts: Dict[str, AbstractAccount], max_transactions: Optional[int] = None) -> List[Transaction]:
        processed = []
        count = 0
        
        while True:
            if max_transactions and count >= max_transactions:
                break
            
            result = self.process_next(accounts)
            if result is None:
                break
            
            processed.append(result)
            count += 1
        
        return processed
    
    def retry_failed(self, accounts: Dict[str, AbstractAccount]) -> List[Transaction]:
        retryable = self._queue.retry_failed()
        processed = []
        
        for transaction in retryable:
            result = self.process_next(accounts)
            if result:
                processed.append(result)
        
        return processed
    
    def get_statistics(self) -> dict:
        return {
            'queue_stats': self._queue.get_statistics(),
            'processed_total': self.processed_count,
            'errors_count': len(self._errors),
            'errors': self._errors[-10:]
        }
    
    def __str__(self) -> str:
        stats = self.get_statistics()
        return (
            f"Обработчик транзакций: "
            f"обработано {stats['processed_total']}, "
            f"ошибок {stats['errors_count']}"
        )