"""
БАНКОВСКАЯ СИСТЕМА
Объектно-ориентированная банковская платформа

Полная демонстрация работы системы:
- Создание банка, клиентов и счетов
- Генерация и обработка транзакций
- Аудит и анализ рисков
- Отчётность и визуализация
"""

from models.account import (
    BankAccount,
    SavingsAccount,
    PremiumAccount,
    InvestmentAccount,
    Currency
)
from models.client import Client
from models.bank import Bank
from models.transaction import (
    Transaction,
    TransactionType,
    TransactionPriority
)
from models.transaction_processor import TransactionProcessor
from models.audit import AuditLog
from models.risk import RiskAnalyzer
from models.report import ReportBuilder, ReportType, ReportFormat

import random
import os


def main():
    """Главная функция запуска банковской системы"""
    
    print("=" * 70)
    print(" БАНКОВСКАЯ СИСТЕМА")
    print(" Объектно-ориентированная платформа")
    print("=" * 70)
    
    # ============================================================
    # ШАГ 1: ИНИЦИАЛИЗАЦИЯ
    # ============================================================
    
    print("\n[1] ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ")
    print("-" * 50)
    
    # Создаём банк
    bank = Bank("Мой Банк")
    print(f"  Создан банк: {bank}")
    
    # Создаём систему аудита
    audit = AuditLog("audit.log")
    print(f"  Создан аудит-лог")
    
    # Создаём анализатор рисков
    risk_analyzer = RiskAnalyzer(audit)
    print(f"  Создан анализатор рисков")
    
    # Создаём обработчик транзакций
    processor = TransactionProcessor()
    print(f"  Создан обработчик транзакций")
    
    # ============================================================
    # ШАГ 2: СОЗДАНИЕ КЛИЕНТОВ
    # ============================================================
    
    print("\n[2] СОЗДАНИЕ КЛИЕНТОВ")
    print("-" * 50)
    
    clients_data = [
        {"name": "Иван Петров", "age": 35, "phone": "+7-999-111-11-11", "email": "ivan@mail.ru"},
        {"name": "Мария Смирнова", "age": 28, "phone": "+7-999-222-22-22", "email": "maria@mail.ru"},
        {"name": "Алексей Козлов", "age": 42, "phone": "+7-999-333-33-33", "email": "alex@mail.ru"},
        {"name": "Елена Васильева", "age": 31, "phone": "+7-999-444-44-44", "email": "elena@mail.ru"},
        {"name": "Дмитрий Соколов", "age": 27, "phone": "+7-999-555-55-55", "email": "dmitry@mail.ru"},
    ]
    
    clients = []
    for i, data in enumerate(clients_data, 1):
        client_id = f"C{i:03d}"
        client = Client(
            full_name=data["name"],
            client_id=client_id,
            age=data["age"],
            phone=data["phone"],
            email=data["email"]
        )
        bank.add_client(client)
        clients.append(client)
        print(f"  {client}")
    
    print(f"  Всего клиентов: {len(clients)}")
    
    # ============================================================
    # ШАГ 3: ОТКРЫТИЕ СЧЕТОВ
    # ============================================================
    
    print("\n[3] ОТКРЫТИЕ СЧЕТОВ")
    print("-" * 50)
    
    accounts = {}
    
    for client in clients:
        # Обычный счёт
        acc1 = BankAccount(
            owner=client.full_name,
            balance=10000 + (hash(client.client_id) % 90000),
            currency=Currency.RUB
        )
        bank.open_account(client.client_id, acc1)
        accounts[acc1.account_id] = acc1
        print(f"  {client.full_name}: {acc1}")
        
        # Второй счёт (разного типа)
        if hash(client.client_id) % 3 == 0:
            acc2 = SavingsAccount(
                owner=client.full_name,
                balance=5000 + (hash(client.client_id) % 20000),
                currency=Currency.RUB,
                min_balance=500,
                monthly_interest_rate=0.05
            )
        elif hash(client.client_id) % 3 == 1:
            acc2 = PremiumAccount(
                owner=client.full_name,
                balance=20000 + (hash(client.client_id) % 50000),
                currency=Currency.USD,
                overdraft_limit=10000,
                monthly_fee=300
            )
        else:
            acc2 = InvestmentAccount(
                owner=client.full_name,
                balance=15000 + (hash(client.client_id) % 30000),
                currency=Currency.EUR
            )
            acc2.add_stock(5000)
            acc2.add_bond(3000)
        
        bank.open_account(client.client_id, acc2)
        accounts[acc2.account_id] = acc2
        print(f"    {acc2}")
    
    print(f"  Всего счетов: {len(accounts)}")
    
    audit.info("Система инициализирована", "system", {
        "clients": len(clients),
        "accounts": len(accounts)
    })
    
    # ============================================================
    # ШАГ 4: ГЕНЕРАЦИЯ ТРАНЗАКЦИЙ
    # ============================================================
    
    print("\n[4] ГЕНЕРАЦИЯ ТРАНЗАКЦИЙ")
    print("-" * 50)
    
    account_ids = list(accounts.keys())
    transactions = []
    
    for i in range(35):
        sender_id = random.choice(account_ids)
        receiver_id = random.choice(account_ids)
        
        while receiver_id == sender_id:
            receiver_id = random.choice(account_ids)
        
        sender = accounts[sender_id]
        receiver = accounts[receiver_id]
        
        tx_type = random.choices(
            [TransactionType.TRANSFER, TransactionType.WITHDRAW, 
             TransactionType.DEPOSIT, TransactionType.EXTERNAL],
            weights=[40, 25, 25, 10]
        )[0]
        
        amount = random.randint(100, 50000)
        
        # Иногда крупная сумма (подозрительная)
        if i % 7 == 0:
            amount = random.randint(100000, 200000)
        
        # Иногда внешний перевод
        is_external = (tx_type == TransactionType.EXTERNAL)
        
        if tx_type == TransactionType.DEPOSIT:
            tx = Transaction(
                transaction_type=tx_type,
                amount=amount,
                currency=sender.currency.value,
                receiver=sender_id
            )
        elif tx_type == TransactionType.WITHDRAW:
            tx = Transaction(
                transaction_type=tx_type,
                amount=amount,
                currency=sender.currency.value,
                sender=sender_id
            )
        else:
            tx = Transaction(
                transaction_type=tx_type,
                amount=amount,
                currency=sender.currency.value,
                sender=sender_id,
                receiver=receiver_id,
                is_external=is_external
            )
        
        # Приоритет
        if i % 5 == 0:
            priority = TransactionPriority.CRITICAL
        elif i % 3 == 0:
            priority = TransactionPriority.HIGH
        else:
            priority = TransactionPriority.NORMAL
        
        # Проверка риска
        client_id = None
        for client in clients:
            if sender_id in client.account_ids:
                client_id = client.client_id
                break
        
        blocked, reasons = risk_analyzer.is_operation_blocked(tx, accounts, client_id)
        
        if blocked:
            tx.mark_failed(f"Заблокировано: {', '.join(reasons)}")
            transactions.append(tx)
            print(f"  БЛОКИРОВАНА: {tx.transaction_id[:6]}... -> {reasons[0] if reasons else 'Неизвестная причина'}")
            continue
        
        # Добавляем в очередь
        delay = 0
        if i % 8 == 0:
            delay = 30
        
        processor.add_transaction(tx, priority, delay)
        transactions.append(tx)
        print(f"  ДОБАВЛЕНА: {tx.transaction_id[:6]}... | {tx.amount:.0f} {tx.currency} | {tx_type.value}")
    
    print(f"\n  Всего транзакций: {len(transactions)}")
    
    stats = processor.queue.get_statistics()
    print(f"  В очереди: {stats['pending']}")
    print(f"  Отложено: {stats['delayed']}")
    
    audit.info("Транзакции сгенерированы", "transaction", {"count": len(transactions)})
    
    # ============================================================
    # ШАГ 5: ОБРАБОТКА ТРАНЗАКЦИЙ
    # ============================================================
    
    print("\n[5] ОБРАБОТКА ТРАНЗАКЦИЙ")
    print("-" * 50)
    
    processed = 0
    failed = 0
    
    while True:
        result = processor.process_next(accounts)
        if result is None:
            break
        
        processed += 1
        if result.status.value == "failed":
            failed += 1
            print(f"  ОШИБКА: {result.transaction_id[:6]}... -> {result.fail_reason}")
        else:
            print(f"  ВЫПОЛНЕНА: {result.transaction_id[:6]}... | {result.amount:.0f} {result.currency}")
    
    print(f"\n  Обработано: {processed}")
    print(f"  Успешно: {processed - failed}")
    print(f"  Ошибок: {failed}")
    
    # Повторные попытки
    if failed > 0:
        print("\n  Повторные попытки:")
        retried = processor.retry_failed(accounts)
        for tx in retried:
            if tx.status.value == "completed":
                print(f"    УСПЕШНО: {tx.transaction_id[:6]}...")
            else:
                print(f"    СНОВА ОШИБКА: {tx.transaction_id[:6]}...")
    
    # ============================================================
    # ШАГ 6: ОТОБРАЖЕНИЕ СОСТОЯНИЯ
    # ============================================================
    
    print("\n[6] СОСТОЯНИЕ СИСТЕМЫ")
    print("-" * 50)
    
    # Клиенты и их счета
    for client in clients[:3]:
        print(f"\n  {client.full_name} ({client.client_id}):")
        total = 0
        for acc_id in client.account_ids:
            if acc_id in accounts:
                acc = accounts[acc_id]
                print(f"    {acc}")
                total += acc.balance
        print(f"    Итого: {total:.2f}")
    
    # Общий баланс
    print(f"\n  Общий баланс банка: {bank.get_total_balance():.2f}")
    
    # Рейтинг
    print("\n  Топ-3 клиента по балансу:")
    ranking = bank.get_clients_ranking()
    for rank, (client_id, balance) in enumerate(ranking[:3], 1):
        client = bank.get_client(client_id)
        print(f"    {rank}. {client.full_name}: {balance:.2f}")
    
    # ============================================================
    # ШАГ 7: ОТЧЁТНОСТЬ
    # ============================================================
    
    print("\n[7] ГЕНЕРАЦИЯ ОТЧЁТОВ")
    print("-" * 50)
    
    report_builder = ReportBuilder(bank, audit, risk_analyzer, processor)
    
    # Банковский отчёт
    bank_report = report_builder.generate_bank_report(ReportFormat.TEXT)
    print("\n  БАНКОВСКИЙ ОТЧЁТ:")
    print("-" * 30)
    if len(bank_report) > 400:
        print(bank_report[:400] + "\n  ...")
    else:
        print(bank_report)
    
    # Отчёт по рискам
    risk_report = report_builder.generate_risk_report(ReportFormat.TEXT)
    print("\n  ОТЧЁТ ПО РИСКАМ:")
    print("-" * 30)
    if len(risk_report) > 400:
        print(risk_report[:400] + "\n  ...")
    else:
        print(risk_report)
    
    # Экспорт отчётов
    json_file = report_builder.export_to_json(ReportType.FULL)
    print(f"\n  Полный отчёт экспортирован: {json_file}")
    
    # ============================================================
    # ШАГ 8: ГРАФИКИ
    # ============================================================
    
    print("\n[8] ГЕНЕРАЦИЯ ГРАФИКОВ")
    print("-" * 50)
    
    try:
        charts = report_builder.generate_all_charts()
        for name, path in charts.items():
            if path and not str(path).startswith("Ошибка"):
                print(f"  {name}: {path}")
            else:
                print(f"  {name}: {path}")
    except Exception as e:
        print(f"  Ошибка: {e}")
    
    # ============================================================
    # ИТОГИ
    # ============================================================
    
    print("\n" + "=" * 70)
    print(" БАНКОВСКАЯ СИСТЕМА УСПЕШНО ЗАВЕРШИЛА РАБОТУ")
    print("=" * 70)
    
    stats = processor.get_statistics()
    print(f"\n  ИТОГОВАЯ СТАТИСТИКА:")
    print(f"    Клиентов: {len(clients)}")
    print(f"    Счетов: {len(accounts)}")
    print(f"    Транзакций: {len(transactions)}")
    print(f"    Обработано: {stats['processed_total']}")
    print(f"    Ошибок: {stats['errors_count']}")
    
    print(f"\n  СОЗДАННЫЕ ФАЙЛЫ:")
    print(f"    audit.log")
    print(f"    reports/ - JSON и CSV отчёты")
    print(f"    charts/ - PNG графики")
    
    print("\n" + "=" * 70)
    print("  СИСТЕМА ГОТОВА К ИСПОЛЬЗОВАНИЮ")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем")
    except Exception as e:
        print(f"\n\n[КРИТИЧЕСКАЯ ОШИБКА] {e}")
        import traceback
        traceback.print_exc()