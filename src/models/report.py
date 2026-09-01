"""
Система отчётности и визуализации
"""

import json
import csv
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import os

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class ReportType:
    CLIENT = "client"
    BANK = "bank"
    RISK = "risk"
    TRANSACTIONS = "transactions"
    FULL = "full"


class ReportFormat:
    TEXT = "text"
    JSON = "json"
    CSV = "csv"


class ReportBuilder:
    """
    Построитель отчётов для банковской системы
    """
    
    def __init__(self, bank=None, audit=None, risk_analyzer=None, processor=None):
        self.bank = bank
        self.audit = audit
        self.risk_analyzer = risk_analyzer
        self.processor = processor
        self._charts_dir = "charts"
        self._reports_dir = "reports"
        
        os.makedirs(self._charts_dir, exist_ok=True)
        os.makedirs(self._reports_dir, exist_ok=True)
    
    def _format_currency(self, amount: float) -> str:
        return f"{amount:,.2f}"
    
    def _get_timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def generate_client_report(self, client_id: str, format_type: str = ReportFormat.TEXT) -> str:
        if not self.bank:
            return "Ошибка: банк не подключён"
        
        client = self.bank.get_client(client_id)
        if not client:
            return f"Клиент {client_id} не найден"
        
        data = {
            'report_type': 'client',
            'client_id': client.client_id,
            'full_name': client.full_name,
            'age': client.age,
            'phone': client.phone,
            'email': client.email,
            'status': 'Заблокирован' if client.is_blocked else 'Активен',
            'is_suspicious': client.is_suspicious,
            'failed_login_attempts': client.failed_login_attempts,
            'suspicious_actions': client.suspicious_actions,
            'accounts': [],
            'total_balance': 0,
            'account_count': len(client.account_ids)
        }
        
        for acc_id in client.account_ids:
            if acc_id in self.bank._accounts:
                acc = self.bank._accounts[acc_id]
                data['accounts'].append({
                    'account_id': acc.account_id,
                    'type': acc.__class__.__name__,
                    'balance': acc.balance,
                    'currency': acc.currency.value,
                    'status': str(acc.status)
                })
                data['total_balance'] += acc.balance
        
        if self.risk_analyzer:
            risk = self.risk_analyzer.get_client_risk_profile(client_id)
            data['risk_profile'] = risk.name
        
        if format_type == ReportFormat.JSON:
            return self._to_json(data)
        elif format_type == ReportFormat.CSV:
            return self._client_to_csv(data)
        else:
            return self._client_to_text(data)
    
    def _client_to_text(self, data: Dict[str, Any]) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append(f"ОТЧЁТ ПО КЛИЕНТУ: {data['full_name']} ({data['client_id']})")
        lines.append("=" * 70)
        lines.append(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("--- ОСНОВНАЯ ИНФОРМАЦИЯ ---")
        lines.append(f"  ФИО: {data['full_name']}")
        lines.append(f"  Возраст: {data['age']}")
        lines.append(f"  Телефон: {data['phone']}")
        lines.append(f"  Email: {data['email']}")
        lines.append(f"  Статус: {data['status']}")
        lines.append(f"  Риск-профиль: {data.get('risk_profile', 'Н/Д')}")
        lines.append(f"  Подозрительный: {'Да' if data['is_suspicious'] else 'Нет'}")
        lines.append(f"  Неудачных попыток входа: {data['failed_login_attempts']}")
        lines.append("")
        lines.append("--- СЧЕТА ---")
        lines.append(f"  Всего счетов: {data['account_count']}")
        lines.append(f"  Общий баланс: {self._format_currency(data['total_balance'])}")
        lines.append("")
        lines.append("  Детали счетов:")
        for acc in data['accounts']:
            lines.append(f"    • {acc['type']} | {acc['account_id']} | "
                        f"{self._format_currency(acc['balance'])} {acc['currency']} | "
                        f"Статус: {acc['status']}")
        lines.append("")
        if data.get('suspicious_actions'):
            lines.append("--- ПОДОЗРИТЕЛЬНЫЕ ДЕЙСТВИЯ ---")
            for action in data['suspicious_actions']:
                lines.append(f"  • {action}")
        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)
    
    def _client_to_csv(self, data: Dict[str, Any]) -> str:
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Поле', 'Значение'])
        writer.writerow(['client_id', data['client_id']])
        writer.writerow(['full_name', data['full_name']])
        writer.writerow(['age', data['age']])
        writer.writerow(['phone', data['phone']])
        writer.writerow(['email', data['email']])
        writer.writerow(['status', data['status']])
        writer.writerow(['risk_profile', data.get('risk_profile', 'N/A')])
        writer.writerow(['total_balance', data['total_balance']])
        writer.writerow(['account_count', data['account_count']])
        
        for acc in data['accounts']:
            writer.writerow(['account', f"{acc['type']}|{acc['account_id']}|{acc['balance']}|{acc['currency']}|{acc['status']}"])
        
        return output.getvalue()
    
    def generate_bank_report(self, format_type: str = ReportFormat.TEXT) -> str:
        if not self.bank:
            return "Ошибка: банк не подключён"
        
        data = {
            'report_type': 'bank',
            'bank_name': self.bank.name,
            'timestamp': datetime.now().isoformat(),
            'clients_count': len(self.bank.clients),
            'accounts_count': len(self.bank.accounts),
            'total_balance': self.bank.get_total_balance(),
            'clients': [],
            'by_currency': {},
            'by_status': {}
        }
        
        for acc in self.bank.accounts:
            curr = acc.currency.value
            data['by_currency'][curr] = data['by_currency'].get(curr, 0) + acc.balance
            
            status = str(acc.status)
            data['by_status'][status] = data['by_status'].get(status, 0) + 1
        
        for client in self.bank.clients:
            total = self.bank.get_client_total_balance(client.client_id)
            data['clients'].append({
                'client_id': client.client_id,
                'name': client.full_name,
                'accounts': len(client.account_ids),
                'balance': total
            })
        
        data['ranking'] = self.bank.get_clients_ranking()[:5]
        
        if self.risk_analyzer:
            risk_stats = self.risk_analyzer.get_risk_statistics()
            data['risk_stats'] = risk_stats
        
        if format_type == ReportFormat.JSON:
            return self._to_json(data)
        elif format_type == ReportFormat.CSV:
            return self._bank_to_csv(data)
        else:
            return self._bank_to_text(data)
    
    def _bank_to_text(self, data: Dict[str, Any]) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append(f"ОТЧЁТ ПО БАНКУ: {data['bank_name']}")
        lines.append("=" * 70)
        lines.append(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("--- ОБЩАЯ СТАТИСТИКА ---")
        lines.append(f"  Клиентов: {data['clients_count']}")
        lines.append(f"  Счетов: {data['accounts_count']}")
        lines.append(f"  Общий баланс: {self._format_currency(data['total_balance'])}")
        lines.append("")
        lines.append("--- ПО ВАЛЮТАМ ---")
        for curr, amount in data['by_currency'].items():
            lines.append(f"  {curr}: {self._format_currency(amount)}")
        lines.append("")
        lines.append("--- ПО СТАТУСАМ СЧЕТОВ ---")
        for status, count in data['by_status'].items():
            lines.append(f"  {status}: {count}")
        lines.append("")
        lines.append("--- ТОП-5 КЛИЕНТОВ ПО БАЛАНСУ ---")
        for rank, (client_id, balance) in enumerate(data['ranking'], 1):
            client = self.bank.get_client(client_id)
            name = client.full_name if client else client_id
            lines.append(f"  {rank}. {name}: {self._format_currency(balance)}")
        lines.append("")
        if 'risk_stats' in data:
            lines.append("--- СТАТИСТИКА РИСКОВ ---")
            risk_stats = data['risk_stats']
            lines.append(f"  Подозрительных операций: {risk_stats.get('total_suspicious', 0)}")
            lines.append(f"  Клиентов с высоким риском: {risk_stats.get('high_risk_clients', 0)}")
            lines.append(f"  Клиентов с критическим риском: {risk_stats.get('critical_risk_clients', 0)}")
        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)
    
    def _bank_to_csv(self, data: Dict[str, Any]) -> str:
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Поле', 'Значение'])
        writer.writerow(['bank_name', data['bank_name']])
        writer.writerow(['timestamp', data['timestamp']])
        writer.writerow(['clients_count', data['clients_count']])
        writer.writerow(['accounts_count', data['accounts_count']])
        writer.writerow(['total_balance', data['total_balance']])
        
        writer.writerow([])
        writer.writerow(['Клиент', 'Счетов', 'Баланс'])
        for client in data['clients']:
            writer.writerow([client['name'], client['accounts'], client['balance']])
        
        return output.getvalue()
    
    def generate_risk_report(self, format_type: str = ReportFormat.TEXT) -> str:
        if not self.risk_analyzer:
            return "Ошибка: риск-анализатор не подключён"
        
        suspicious = self.risk_analyzer.get_suspicious_operations()
        
        data = {
            'report_type': 'risk',
            'timestamp': datetime.now().isoformat(),
            'total_suspicious': len(suspicious),
            'by_risk_level': {},
            'suspicious_operations': suspicious[:50],
            'client_profiles': {}
        }
        
        for op in suspicious:
            level = op.get('risk_level', 'UNKNOWN')
            data['by_risk_level'][level] = data['by_risk_level'].get(level, 0) + 1
        
        for client in self.bank.clients if self.bank else []:
            risk = self.risk_analyzer.get_client_risk_profile(client.client_id)
            if risk.value > 0:
                data['client_profiles'][client.client_id] = {
                    'name': client.full_name,
                    'risk': risk.name,
                    'is_blocked': client.is_blocked
                }
        
        if format_type == ReportFormat.JSON:
            return self._to_json(data)
        else:
            return self._risk_to_text(data)
    
    def _risk_to_text(self, data: Dict[str, Any]) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append("ОТЧЁТ ПО РИСКАМ И ПОДОЗРИТЕЛЬНЫМ ОПЕРАЦИЯМ")
        lines.append("=" * 70)
        lines.append(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append(f"Всего подозрительных операций: {data['total_suspicious']}")
        lines.append("")
        lines.append("--- ПО УРОВНЯМ РИСКА ---")
        for level, count in data['by_risk_level'].items():
            lines.append(f"  {level}: {count}")
        lines.append("")
        
        if data['client_profiles']:
            lines.append("--- КЛИЕНТЫ С ПОВЫШЕННЫМ РИСКОМ ---")
            for client_id, info in data['client_profiles'].items():
                status = "БЛОКИРОВАН" if info['is_blocked'] else "АКТИВЕН"
                lines.append(f"  {info['name']} ({client_id}): {info['risk']} - {status}")
            lines.append("")
        
        if data['suspicious_operations']:
            lines.append("--- ПОСЛЕДНИЕ ПОДОЗРИТЕЛЬНЫЕ ОПЕРАЦИИ ---")
            for op in data['suspicious_operations'][:10]:
                lines.append(f"  [{op.get('timestamp', 'N/A')}]")
                lines.append(f"    Клиент: {op.get('client_id', 'N/A')}")
                lines.append(f"    Уровень: {op.get('risk_level', 'N/A')}")
                lines.append(f"    Сумма: {op.get('amount', 0)} {op.get('currency', '')}")
                lines.append(f"    Причины: {', '.join(op.get('reasons', []))}")
                lines.append("")
        
        lines.append("=" * 70)
        return "\n".join(lines)
    
    def _risk_to_csv(self) -> str:
        """Экспорт отчёта по рискам в CSV"""
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Тип отчёта', 'Риски'])
        writer.writerow(['ОТЧЁТ ПО РИСКАМ', ''])
        writer.writerow([])
        writer.writerow(['Время', 'Клиент', 'Уровень риска', 'Сумма', 'Причины'])
        
        suspicious = self.risk_analyzer.get_suspicious_operations() if self.risk_analyzer else []
        for op in suspicious:
            writer.writerow([
                op.get('timestamp', ''),
                op.get('client_id', ''),
                op.get('risk_level', ''),
                op.get('amount', 0),
                ', '.join(op.get('reasons', []))
            ])
        
        return output.getvalue()
    
    def generate_transactions_report(self, format_type: str = ReportFormat.TEXT) -> str:
        if not self.processor:
            return "Ошибка: обработчик транзакций не подключён"
        
        queue_stats = self.processor.queue.get_statistics()
        
        data = {
            'report_type': 'transactions',
            'timestamp': datetime.now().isoformat(),
            'queue_stats': queue_stats,
            'processed_total': self.processor.processed_count,
            'errors': self.processor.get_statistics().get('errors', [])[:10]
        }
        
        if format_type == ReportFormat.JSON:
            return self._to_json(data)
        else:
            return self._transactions_to_text(data)
    
    def _transactions_to_text(self, data: Dict[str, Any]) -> str:
        lines = []
        lines.append("=" * 70)
        lines.append("ОТЧЁТ ПО ТРАНЗАКЦИЯМ")
        lines.append("=" * 70)
        lines.append(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("--- СТАТИСТИКА ОЧЕРЕДИ ---")
        stats = data['queue_stats']
        lines.append(f"  Ожидает: {stats.get('pending', 0)}")
        lines.append(f"  Обрабатывается: {stats.get('processing', 0)}")
        lines.append(f"  Выполнено: {stats.get('completed', 0)}")
        lines.append(f"  Ошибок: {stats.get('failed', 0)}")
        lines.append(f"  Отменено: {stats.get('cancelled', 0)}")
        lines.append(f"  Отложено: {stats.get('delayed', 0)}")
        lines.append(f"  Всего: {stats.get('total', 0)}")
        lines.append("")
        lines.append(f"Всего обработано: {data['processed_total']}")
        lines.append("")
        if data['errors']:
            lines.append("--- ПОСЛЕДНИЕ ОШИБКИ ---")
            for err in data['errors']:
                lines.append(f"  {err}")
        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)
    
    def generate_full_report(self, format_type: str = ReportFormat.TEXT) -> str:
        parts = []
        parts.append("=" * 70)
        parts.append("ПОЛНЫЙ ОТЧЁТ ПО БАНКОВСКОЙ СИСТЕМЕ")
        parts.append("=" * 70)
        parts.append(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        parts.append("")
        
        parts.append(self.generate_bank_report(ReportFormat.TEXT))
        parts.append("")
        parts.append(self.generate_transactions_report(ReportFormat.TEXT))
        parts.append("")
        parts.append(self.generate_risk_report(ReportFormat.TEXT))
        
        return "\n".join(parts)
    
    def _to_json(self, data: Dict[str, Any]) -> str:
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def export_to_json(self, report_type: str, filename: Optional[str] = None, client_id: Optional[str] = None) -> str:
        if not filename:
            filename = f"{report_type}_{self._get_timestamp()}.json"
        
        filepath = os.path.join(self._reports_dir, filename)
        
        if report_type == ReportType.CLIENT:
            if not client_id:
                return "Ошибка: для клиентского отчёта укажите client_id"
            content = self.generate_client_report(client_id, ReportFormat.JSON)
        elif report_type == ReportType.BANK:
            content = self.generate_bank_report(ReportFormat.JSON)
        elif report_type == ReportType.RISK:
            content = self.generate_risk_report(ReportFormat.JSON)
        elif report_type == ReportType.TRANSACTIONS:
            content = self.generate_transactions_report(ReportFormat.JSON)
        elif report_type == ReportType.FULL:
            data = {
                'report_type': 'full',
                'timestamp': datetime.now().isoformat(),
                'bank': json.loads(self.generate_bank_report(ReportFormat.JSON)),
                'transactions': json.loads(self.generate_transactions_report(ReportFormat.JSON)),
                'risk': json.loads(self.generate_risk_report(ReportFormat.JSON))
            }
            content = json.dumps(data, ensure_ascii=False, indent=2)
        else:
            return f"Неизвестный тип отчёта: {report_type}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def export_to_csv(self, report_type: str, filename: Optional[str] = None) -> str:
        if not filename:
            filename = f"{report_type}_{self._get_timestamp()}.csv"
        
        filepath = os.path.join(self._reports_dir, filename)
        
        if report_type == ReportType.BANK:
            content = self.generate_bank_report(ReportFormat.CSV)
        elif report_type == ReportType.RISK:
            content = self._risk_to_csv()
        else:
            return f"CSV экспорт для {report_type} не поддерживается"
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        
        return filepath
    
    def export_client_csv(self, client_id: str, filename: Optional[str] = None) -> str:
        if not filename:
            filename = f"client_{client_id}_{self._get_timestamp()}.csv"
        
        filepath = os.path.join(self._reports_dir, filename)
        content = self.generate_client_report(client_id, ReportFormat.CSV)
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        
        return filepath
    
    def save_report(self, content: str, filename: str) -> str:
        filepath = os.path.join(self._reports_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def create_pie_chart(self, data: Dict[str, float], title: str, filename: str) -> Optional[str]:
        if not MATPLOTLIB_AVAILABLE:
            return "Ошибка: matplotlib не установлен"
        
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            labels = list(data.keys())
            values = list(data.values())
            
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.set_title(title)
            
            filepath = os.path.join(self._charts_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            return filepath
        except Exception as e:
            return f"Ошибка создания диаграммы: {e}"
    
    def create_bar_chart(self, data: Dict[str, Any], title: str, xlabel: str, ylabel: str, filename: str) -> Optional[str]:
        if not MATPLOTLIB_AVAILABLE:
            return "Ошибка: matplotlib не установлен"
        
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            labels = list(data.keys())
            values = list(data.values())
            
            bars = ax.bar(labels, values)
            ax.set_title(title)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.annotate(f'{value:,.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom')
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            filepath = os.path.join(self._charts_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            return filepath
        except Exception as e:
            return f"Ошибка создания диаграммы: {e}"
    
    def create_balance_chart(self, account_id: str, filename: str) -> Optional[str]:
        if not MATPLOTLIB_AVAILABLE:
            return "Ошибка: matplotlib не установлен"
        
        if not self.bank:
            return "Ошибка: банк не подключён"
        
        if account_id not in self.bank._accounts:
            return f"Счёт {account_id} не найден"
        
        account = self.bank._accounts[account_id]
        history = account.get_transaction_history()
        
        if not history:
            return "Нет истории транзакций для построения графика"
        
        try:
            dates = []
            balances = []
            
            for entry in history:
                dates.append(entry['timestamp'].strftime('%Y-%m-%d %H:%M'))
                balances.append(entry['balance_after'])
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(dates, balances, marker='o', linestyle='-', linewidth=2)
            ax.set_title(f"Движение баланса: {account.owner} ({account_id})")
            ax.set_xlabel("Дата")
            ax.set_ylabel(f"Баланс ({account.currency.value})")
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            filepath = os.path.join(self._charts_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            return filepath
        except Exception as e:
            return f"Ошибка создания графика: {e}"
    
    def generate_all_charts(self) -> Dict[str, str]:
        results = {}
        
        if not self.bank:
            return {"error": "Банк не подключён"}
        
        by_currency = {}
        for acc in self.bank.accounts:
            curr = acc.currency.value
            by_currency[curr] = by_currency.get(curr, 0) + acc.balance
        
        if by_currency:
            result = self.create_pie_chart(
                by_currency,
                "Распределение баланса по валютам",
                f"currency_pie_{self._get_timestamp()}.png"
            )
            results['currency_pie'] = result
        
        ranking = self.bank.get_clients_ranking()[:10]
        if ranking:
            client_data = {}
            for client_id, balance in ranking:
                client = self.bank.get_client(client_id)
                name = client.full_name[:15] + "..." if client and len(client.full_name) > 15 else (client.full_name if client else client_id)
                client_data[name] = balance
            
            result = self.create_bar_chart(
                client_data,
                "Топ-10 клиентов по балансу",
                "Клиент",
                "Баланс",
                f"ranking_bar_{self._get_timestamp()}.png"
            )
            results['ranking_bar'] = result
        
        by_status = {}
        for acc in self.bank.accounts:
            status = str(acc.status)
            by_status[status] = by_status.get(status, 0) + 1
        
        if by_status:
            result = self.create_pie_chart(
                by_status,
                "Распределение счетов по статусам",
                f"status_pie_{self._get_timestamp()}.png"
            )
            results['status_pie'] = result
        
        return results