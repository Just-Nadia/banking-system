"""
Модель аудита и логирования
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import json
import os


class LogLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class AuditLog:
    """
    Система аудита для логирования всех операций
    """
    
    def __init__(self, log_file: str = "audit.log"):
        self._logs: List[Dict[str, Any]] = []
        self._log_file = log_file
        self._enabled = True
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def enable(self) -> None:
        self._enabled = True
    
    def disable(self) -> None:
        self._enabled = False
    
    def log(
        self,
        level: LogLevel,
        message: str,
        category: str = "general",
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        if not self._enabled:
            return
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.name,
            'level_value': level.value,
            'category': category,
            'message': message,
            'data': data or {}
        }
        
        self._logs.append(log_entry)
        self._save_to_file(log_entry)
    
    def info(self, message: str, category: str = "general", data: Optional[Dict[str, Any]] = None) -> None:
        self.log(LogLevel.INFO, message, category, data)
    
    def warning(self, message: str, category: str = "general", data: Optional[Dict[str, Any]] = None) -> None:
        self.log(LogLevel.WARNING, message, category, data)
    
    def error(self, message: str, category: str = "general", data: Optional[Dict[str, Any]] = None) -> None:
        self.log(LogLevel.ERROR, message, category, data)
    
    def critical(self, message: str, category: str = "general", data: Optional[Dict[str, Any]] = None) -> None:
        self.log(LogLevel.CRITICAL, message, category, data)
    
    def debug(self, message: str, category: str = "general", data: Optional[Dict[str, Any]] = None) -> None:
        self.log(LogLevel.DEBUG, message, category, data)
    
    def _save_to_file(self, log_entry: Dict[str, Any]) -> None:
        try:
            with open(self._log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception:
            pass
    
    def filter(
        self,
        level: Optional[LogLevel] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        result = self._logs.copy()
        
        if level is not None:
            result = [log for log in result if log['level_value'] >= level.value]
        
        if category is not None:
            result = [log for log in result if log['category'] == category]
        
        if start_date is not None:
            result = [log for log in result if datetime.fromisoformat(log['timestamp']) >= start_date]
        
        if end_date is not None:
            result = [log for log in result if datetime.fromisoformat(log['timestamp']) <= end_date]
        
        result.sort(key=lambda x: x['timestamp'], reverse=True)
        return result[:limit]
    
    def get_by_level(self, level: LogLevel) -> List[Dict[str, Any]]:
        return self.filter(level=level)
    
    def get_errors(self) -> List[Dict[str, Any]]:
        return self.filter(level=LogLevel.ERROR)
    
    def get_critical(self) -> List[Dict[str, Any]]:
        return self.filter(level=LogLevel.CRITICAL)
    
    def get_recent(self, count: int = 10) -> List[Dict[str, Any]]:
        return self.filter(limit=count)
    
    def clear(self) -> None:
        self._logs.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        stats = {
            'total': len(self._logs),
            'by_level': {},
            'by_category': {},
            'last_entry': None
        }
        
        for log in self._logs:
            level = log['level']
            stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
            
            category = log['category']
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        
        if self._logs:
            stats['last_entry'] = self._logs[-1]['timestamp']
        
        return stats
    
    def export_to_file(self, filename: str) -> None:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self._logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка экспорта логов: {e}")
    
    def __str__(self) -> str:
        stats = self.get_statistics()
        return f"AuditLog: {stats['total']} записей, последняя: {stats['last_entry']}"