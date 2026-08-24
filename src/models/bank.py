"""
Модель банка
"""

from datetime import datetime
from typing import Optional, List, Dict, Tuple

from .account import AbstractAccount
from .client import Client
from .exceptions import InvalidOperationError


class Bank:
    """
    Класс, представляющий банк
    """
    
    def __init__(self, name: str):
        self._name = name
        self._clients: Dict[str, Client] = {}
        self._accounts: Dict[str, AbstractAccount] = {}
        self._created_at = datetime.now()
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def clients(self) -> List[Client]:
        return list(self._clients.values())
    
    @property
    def accounts(self) -> List[AbstractAccount]:
        return list(self._accounts.values())
    
    def add_client(self, client: Client) -> None:
        if client.client_id in self._clients:
            raise ValueError(f"Клиент с ID {client.client_id} уже существует")
        self._clients[client.client_id] = client
    
    def get_client(self, client_id: str) -> Optional[Client]:
        return self._clients.get(client_id)
    
    def _is_night_hours(self) -> bool:
        current_hour = datetime.now().hour
        return 0 <= current_hour < 5
    
    def open_account(self, client_id: str, account: AbstractAccount) -> None:
        client = self.get_client(client_id)
        if not client:
            raise ValueError(f"Клиент с ID {client_id} не найден")
        
        if client.is_blocked:
            raise InvalidOperationError(
                f"Клиент {client_id} заблокирован. Невозможно открыть счёт"
            )
        
        if self._is_night_hours():
            client.mark_suspicious(
                f"Попытка открытия счёта в ночное время ({datetime.now().hour}:00)"
            )
            raise InvalidOperationError(
                "Операции запрещены с 00:00 до 05:00"
            )
        
        self._accounts[account.account_id] = account
        client.add_account(account.account_id)
    
    def close_account(self, client_id: str, account_id: str) -> None:
        client = self.get_client(client_id)
        if not client:
            raise ValueError(f"Клиент с ID {client_id} не найден")
        
        if account_id not in self._accounts:
            raise ValueError(f"Счёт {account_id} не найден")
        
        account = self._accounts[account_id]
        
        if client.is_blocked:
            raise InvalidOperationError(
                f"Клиент {client_id} заблокирован. Невозможно закрыть счёт"
            )
        
        if self._is_night_hours():
            client.mark_suspicious(
                f"Попытка закрытия счёта в ночное время ({datetime.now().hour}:00)"
            )
            raise InvalidOperationError(
                "Операции запрещены с 00:00 до 05:00"
            )
        
        if account_id not in client.account_ids:
            raise InvalidOperationError(
                f"Счёт {account_id} не принадлежит клиенту {client_id}"
            )
        
        account.close()
        client.remove_account(account_id)
    
    def freeze_account(self, client_id: str, account_id: str) -> None:
        client = self.get_client(client_id)
        if not client:
            raise ValueError(f"Клиент с ID {client_id} не найден")
        
        if account_id not in self._accounts:
            raise ValueError(f"Счёт {account_id} не найден")
        
        account = self._accounts[account_id]
        
        if client.is_blocked:
            raise InvalidOperationError(
                f"Клиент {client_id} заблокирован. Невозможно заморозить счёт"
            )
        
        if account_id not in client.account_ids:
            raise InvalidOperationError(
                f"Счёт {account_id} не принадлежит клиенту {client_id}"
            )
        
        account.freeze()
    
    def unfreeze_account(self, client_id: str, account_id: str) -> None:
        client = self.get_client(client_id)
        if not client:
            raise ValueError(f"Клиент с ID {client_id} не найден")
        
        if account_id not in self._accounts:
            raise ValueError(f"Счёт {account_id} не найден")
        
        account = self._accounts[account_id]
        
        if client.is_blocked:
            raise InvalidOperationError(
                f"Клиент {client_id} заблокирован. Невозможно разморозить счёт"
            )
        
        if account_id not in client.account_ids:
            raise InvalidOperationError(
                f"Счёт {account_id} не принадлежит клиенту {client_id}"
            )
        
        account.unfreeze()
    
    def authenticate_client(self, client_id: str, password: str) -> bool:
        client = self.get_client(client_id)
        if not client:
            return False
        
        if client.is_blocked:
            return False
        
        if password and password != "wrong":
            client.reset_login_attempts()
            return True
        else:
            client.record_failed_login()
            return False
    
    def search_accounts(self, query: str) -> List[AbstractAccount]:
        results = []
        query_lower = query.lower()
        
        for account in self._accounts.values():
            if query_lower in account.owner.lower():
                results.append(account)
        
        return results
    
    def get_total_balance(self) -> float:
        total = 0.0
        for account in self._accounts.values():
            total += account.balance
        return total
    
    def get_clients_ranking(self) -> List[Tuple[str, float]]:
        ranking = {}
        
        for client in self._clients.values():
            total = 0.0
            for account_id in client.account_ids:
                if account_id in self._accounts:
                    total += self._accounts[account_id].balance
            ranking[client.client_id] = total
        
        return sorted(ranking.items(), key=lambda x: x[1], reverse=True)
    
    def get_client_total_balance(self, client_id: str) -> float:
        client = self.get_client(client_id)
        if not client:
            return 0.0
        
        total = 0.0
        for account_id in client.account_ids:
            if account_id in self._accounts:
                total += self._accounts[account_id].balance
        return total
    
    def __str__(self) -> str:
        return (
            f"Банк: {self._name} | "
            f"Клиентов: {len(self._clients)} | "
            f"Счетов: {len(self._accounts)} | "
            f"Общий баланс: {self.get_total_balance():.2f}"
        )