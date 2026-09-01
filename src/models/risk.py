"""
Модель анализа рисков
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple

from .transaction import Transaction
from .audit import LogLevel


class RiskLevel(Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class RiskAnalyzer:
    """
    Анализатор рисков для выявления подозрительных операций
    """
    
    THRESHOLDS = {
        'large_amount': 100000.0,
        'max_frequency': 5,
        'night_hours_start': 0,
        'night_hours_end': 5,
        'new_account_days': 7,
    }
    
    def __init__(self, audit_log=None):
        self._audit_log = audit_log
        self._suspicious_operations: List[Dict[str, Any]] = []
        self._client_risk_profiles: Dict[str, RiskLevel] = {}
        self._operation_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def set_audit_log(self, audit_log) -> None:
        self._audit_log = audit_log
    
    def _log(self, level, message, category="risk", data=None) -> None:
        if self._audit_log:
            self._audit_log.log(level, message, category, data)
    
    def _check_large_amount(self, transaction: Transaction) -> Tuple[bool, str]:
        if transaction.amount >= self.THRESHOLDS['large_amount']:
            return True, f"Крупная сумма: {transaction.amount:.2f} {transaction.currency}"
        return False, ""
    
    def _check_night_operation(self, transaction: Transaction) -> Tuple[bool, str]:
        current_hour = datetime.now().hour
        if self.THRESHOLDS['night_hours_start'] <= current_hour < self.THRESHOLDS['night_hours_end']:
            return True, f"Операция в ночное время ({current_hour}:00)"
        return False, ""
    
    def _check_frequency(self, sender: str, max_operations: int = 5) -> Tuple[bool, str]:
        if sender not in self._operation_history:
            self._operation_history[sender] = []
        
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        self._operation_history[sender] = [
            op for op in self._operation_history[sender]
            if op['timestamp'] > one_minute_ago
        ]
        
        if len(self._operation_history[sender]) >= self.THRESHOLDS['max_frequency']:
            return True, f"Частые операции: {len(self._operation_history[sender])} за минуту"
        
        return False, ""
    
    def _check_new_account(self, account_id: str, accounts: dict) -> Tuple[bool, str]:
        if account_id in accounts:
            account = accounts[account_id]
            days_old = (datetime.now() - account.created_at).days
            if days_old < self.THRESHOLDS['new_account_days']:
                return True, f"Новый счёт (существует {days_old} дней)"
        return False, ""
    
    def _check_external_transfer(self, transaction: Transaction) -> Tuple[bool, str]:
        if transaction.is_external:
            return True, "Внешний перевод"
        return False, ""
    
    def analyze_transaction(
        self,
        transaction: Transaction,
        accounts: Optional[Dict[str, Any]] = None,
        client_id: Optional[str] = None
    ) -> Tuple[RiskLevel, List[str]]:
        reasons = []
        risk_score = 0
        
        is_suspicious, reason = self._check_large_amount(transaction)
        if is_suspicious:
            reasons.append(reason)
            risk_score += 2
        
        is_suspicious, reason = self._check_night_operation(transaction)
        if is_suspicious:
            reasons.append(reason)
            risk_score += 1
        
        if transaction.sender:
            is_suspicious, reason = self._check_frequency(transaction.sender)
            if is_suspicious:
                reasons.append(reason)
                risk_score += 2
        
        # Проверка новых счетов: по получателю (требование дня 5)
        if transaction.receiver and accounts:
            is_suspicious, reason = self._check_new_account(transaction.receiver, accounts)
            if is_suspicious:
                reasons.append(reason)
                risk_score += 1
        
        is_suspicious, reason = self._check_external_transfer(transaction)
        if is_suspicious:
            reasons.append(reason)
            risk_score += 1
        
        if risk_score >= 5:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 3:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 1:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self._suspicious_operations.append({
                'transaction_id': transaction.transaction_id,
                'risk_level': risk_level.name,
                'reasons': reasons,
                'timestamp': datetime.now().isoformat(),
                'client_id': client_id,
                'amount': transaction.amount,
                'currency': transaction.currency
            })
            
            self._log(
                LogLevel.WARNING if risk_level == RiskLevel.HIGH else LogLevel.CRITICAL,
                f"Подозрительная операция: {', '.join(reasons)}",
                "risk",
                {
                    'transaction_id': transaction.transaction_id,
                    'risk_level': risk_level.name,
                    'client_id': client_id,
                    'amount': transaction.amount
                }
            )
        
        if transaction.sender:
            if transaction.sender not in self._operation_history:
                self._operation_history[transaction.sender] = []
            self._operation_history[transaction.sender].append({
                'transaction_id': transaction.transaction_id,
                'timestamp': datetime.now(),
                'amount': transaction.amount
            })
        
        return risk_level, reasons
    
    def update_client_risk_profile(self, client_id: str, risk_level: RiskLevel) -> None:
        current_risk = self._client_risk_profiles.get(client_id, RiskLevel.LOW)
        if risk_level.value > current_risk.value:
            self._client_risk_profiles[client_id] = risk_level
            
            self._log(
                LogLevel.WARNING,
                f"Обновлён риск-профиль клиента {client_id}: {risk_level.name}",
                "risk",
                {'client_id': client_id, 'risk_level': risk_level.name}
            )
    
    def get_client_risk_profile(self, client_id: str) -> RiskLevel:
        return self._client_risk_profiles.get(client_id, RiskLevel.LOW)
    
    def get_suspicious_operations(self, min_risk: RiskLevel = RiskLevel.MEDIUM) -> List[Dict[str, Any]]:
        result = []
        for op in self._suspicious_operations:
            risk_level = RiskLevel[op['risk_level']]
            if risk_level.value >= min_risk.value:
                result.append(op)
        return result
    
    def is_operation_blocked(
        self,
        transaction: Transaction,
        accounts: Optional[Dict[str, Any]] = None,
        client_id: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        risk_level, reasons = self.analyze_transaction(transaction, accounts, client_id)
        
        if risk_level == RiskLevel.CRITICAL:
            self._log(
                LogLevel.CRITICAL,
                f"ОПЕРАЦИЯ ЗАБЛОКИРОВАНА: {transaction.transaction_id}",
                "security",
                {
                    'transaction_id': transaction.transaction_id,
                    'reasons': reasons,
                    'client_id': client_id
                }
            )
            return True, reasons
        
        if client_id:
            client_risk = self.get_client_risk_profile(client_id)
            if client_risk == RiskLevel.CRITICAL:
                reasons.append("Клиент имеет критический риск-профиль")
                return True, reasons
        
        return False, reasons
    
    def get_risk_statistics(self) -> Dict[str, Any]:
        stats = {
            'total_suspicious': len(self._suspicious_operations),
            'by_risk_level': {},
            'high_risk_clients': 0,
            'critical_risk_clients': 0
        }
        
        for op in self._suspicious_operations:
            level = op['risk_level']
            stats['by_risk_level'][level] = stats['by_risk_level'].get(level, 0) + 1
        
        for client_id, risk in self._client_risk_profiles.items():
            if risk == RiskLevel.HIGH:
                stats['high_risk_clients'] += 1
            elif risk == RiskLevel.CRITICAL:
                stats['critical_risk_clients'] += 1
        
        return stats
    
    def __str__(self) -> str:
        stats = self.get_risk_statistics()
        return (
            f"RiskAnalyzer: {stats['total_suspicious']} подозрительных операций, "
            f"риск-профили: {stats['high_risk_clients']} высоких, "
            f"{stats['critical_risk_clients']} критических"
        )