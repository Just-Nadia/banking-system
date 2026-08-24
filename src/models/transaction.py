"""
Модели транзакций
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field


class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    TRANSFER = "transfer"
    INTERNAL = "internal"
    EXTERNAL = "external"
    FEE = "fee"
    INTEREST = "interest"


class TransactionStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DELAYED = "delayed"


class TransactionPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Transaction:
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    transaction_type: TransactionType = TransactionType.TRANSFER
    amount: float = 0.0
    currency: str = "RUB"
    fee: float = 0.0
    sender: Optional[str] = None
    receiver: Optional[str] = None
    status: TransactionStatus = TransactionStatus.PENDING
    priority: TransactionPriority = TransactionPriority.NORMAL
    fail_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    is_external: bool = False
    
    def mark_completed(self) -> None:
        self.status = TransactionStatus.COMPLETED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def mark_failed(self, reason: str) -> None:
        self.status = TransactionStatus.FAILED
        self.fail_reason = reason
        self.updated_at = datetime.now()
    
    def mark_cancelled(self) -> None:
        self.status = TransactionStatus.CANCELLED
        self.updated_at = datetime.now()
    
    def mark_processing(self) -> None:
        self.status = TransactionStatus.PROCESSING
        self.updated_at = datetime.now()
    
    def mark_delayed(self) -> None:
        self.status = TransactionStatus.DELAYED
        self.updated_at = datetime.now()
    
    def increment_retry(self) -> None:
        self.retry_count += 1
        self.updated_at = datetime.now()
    
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries and self.status in [
            TransactionStatus.FAILED,
            TransactionStatus.DELAYED
        ]
    
    def __str__(self) -> str:
        return (
            f"Транзакция {self.transaction_id} | "
            f"{self.transaction_type.value} | "
            f"{self.amount:.2f} {self.currency} | "
            f"{self.status.value} | "
            f"От: {self.sender} -> Кому: {self.receiver}"
        )
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.transaction_id}, type={self.transaction_type.value})>"


class TransactionQueue:
    def __init__(self):
        self._pending: List[Transaction] = []
        self._processing: List[Transaction] = []
        self._completed: List[Transaction] = []
        self._failed: List[Transaction] = []
        self._cancelled: List[Transaction] = []
        self._delayed: List[Transaction] = []
    
    @property
    def pending_count(self) -> int:
        return len(self._pending)
    
    @property
    def processing_count(self) -> int:
        return len(self._processing)
    
    @property
    def completed_count(self) -> int:
        return len(self._completed)
    
    @property
    def failed_count(self) -> int:
        return len(self._failed)
    
    @property
    def total_count(self) -> int:
        return (self.pending_count + self.processing_count + 
                self.completed_count + self.failed_count + 
                len(self._cancelled) + len(self._delayed))
    
    def add(self, transaction: Transaction) -> None:
        self._pending.append(transaction)
        self._pending.sort(key=lambda t: t.priority.value, reverse=True)
    
    def add_priority(self, transaction: Transaction, priority: TransactionPriority) -> None:
        transaction.priority = priority
        self.add(transaction)
    
    def add_delayed(self, transaction: Transaction, delay_seconds: int = 60) -> None:
        transaction.mark_delayed()
        self._delayed.append(transaction)
    
    def get_next(self) -> Optional[Transaction]:
        if not self._pending:
            return None
        
        transaction = self._pending.pop(0)
        transaction.mark_processing()
        self._processing.append(transaction)
        return transaction
    
    def complete(self, transaction: Transaction) -> None:
        if transaction in self._processing:
            self._processing.remove(transaction)
        transaction.mark_completed()
        self._completed.append(transaction)
    
    def fail(self, transaction: Transaction, reason: str) -> None:
        if transaction in self._processing:
            self._processing.remove(transaction)
        transaction.mark_failed(reason)
        self._failed.append(transaction)
    
    def cancel(self, transaction: Transaction) -> None:
        if transaction in self._pending:
            self._pending.remove(transaction)
        elif transaction in self._delayed:
            self._delayed.remove(transaction)
        elif transaction in self._processing:
            self._processing.remove(transaction)
        transaction.mark_cancelled()
        self._cancelled.append(transaction)
    
    def retry_failed(self) -> List[Transaction]:
        retryable = []
        for transaction in self._failed[:]:
            if transaction.can_retry():
                transaction.increment_retry()
                self._failed.remove(transaction)
                transaction.status = TransactionStatus.PENDING
                self._pending.append(transaction)
                retryable.append(transaction)
        self._pending.sort(key=lambda t: t.priority.value, reverse=True)
        return retryable
    
    def get_all_pending(self) -> List[Transaction]:
        return self._pending.copy()
    
    def get_all_completed(self) -> List[Transaction]:
        return self._completed.copy()
    
    def get_all_failed(self) -> List[Transaction]:
        return self._failed.copy()
    
    def get_statistics(self) -> dict:
        return {
            'pending': self.pending_count,
            'processing': self.processing_count,
            'completed': self.completed_count,
            'failed': self.failed_count,
            'cancelled': len(self._cancelled),
            'delayed': len(self._delayed),
            'total': self.total_count
        }
    
    def __str__(self) -> str:
        stats = self.get_statistics()
        return (
            f"Очередь транзакций: "
            f"ожидает {stats['pending']}, "
            f"обрабатывается {stats['processing']}, "
            f"выполнено {stats['completed']}, "
            f"ошибок {stats['failed']}"
        )