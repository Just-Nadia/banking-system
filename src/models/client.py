"""
Модель клиента банка
"""

from datetime import datetime
from typing import List, Optional


class Client:
    """
    Класс, представляющий клиента банка
    """
    
    def __init__(
        self,
        full_name: str,
        client_id: str,
        age: int,
        phone: str,
        email: str = None
    ):
        if age < 18:
            raise ValueError("Клиент должен быть старше 18 лет")
        
        self._full_name = full_name
        self._client_id = client_id
        self._age = age
        self._phone = phone
        self._email = email
        self._account_ids: List[str] = []
        self._is_blocked = False
        self._failed_login_attempts = 0
        self._is_suspicious = False
        self._suspicious_actions: List[str] = []
        self._created_at = datetime.now()
    
    @property
    def full_name(self) -> str:
        return self._full_name
    
    @property
    def client_id(self) -> str:
        return self._client_id
    
    @property
    def age(self) -> int:
        return self._age
    
    @property
    def phone(self) -> str:
        return self._phone
    
    @property
    def email(self) -> str:
        return self._email
    
    @property
    def account_ids(self) -> List[str]:
        return self._account_ids.copy()
    
    @property
    def is_blocked(self) -> bool:
        return self._is_blocked
    
    @property
    def is_suspicious(self) -> bool:
        return self._is_suspicious
    
    @property
    def failed_login_attempts(self) -> int:
        return self._failed_login_attempts
    
    @property
    def suspicious_actions(self) -> List[str]:
        return self._suspicious_actions.copy()
    
    def add_account(self, account_id: str) -> None:
        if account_id not in self._account_ids:
            self._account_ids.append(account_id)
    
    def remove_account(self, account_id: str) -> None:
        if account_id in self._account_ids:
            self._account_ids.remove(account_id)
    
    def record_failed_login(self) -> None:
        self._failed_login_attempts += 1
        if self._failed_login_attempts >= 3:
            self._is_blocked = True
            self._add_suspicious_action("Заблокирован после 3 неудачных попыток входа")
    
    def reset_login_attempts(self) -> None:
        self._failed_login_attempts = 0
    
    def _add_suspicious_action(self, action: str) -> None:
        self._suspicious_actions.append(f"{datetime.now()}: {action}")
        self._is_suspicious = True
    
    def mark_suspicious(self, action: str) -> None:
        self._add_suspicious_action(action)
    
    def __str__(self) -> str:
        status = "ЗАБЛОКИРОВАН" if self._is_blocked else "АКТИВЕН"
        suspicious = " (ПОДОЗРИТЕЛЬНЫЙ)" if self._is_suspicious else ""
        return (
            f"Клиент: {self._full_name} | "
            f"ID: {self._client_id} | "
            f"Возраст: {self._age} | "
            f"Счетов: {len(self._account_ids)} | "
            f"Статус: {status}{suspicious}"
        )
    
    def __repr__(self) -> str:
        return f"<Client(id={self._client_id}, name={self._full_name})>"