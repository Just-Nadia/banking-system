# Банковская система

Объектно-ориентированная банковская платформа на Python.

---

## Структура проекта

```
banking-system/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── account.py
│   │   ├── client.py
│   │   ├── bank.py
│   │   ├── transaction.py
│   │   ├── transaction_processor.py
│   │   ├── audit.py
│   │   ├── risk.py
│   │   └── report.py
│   └── main.py
├── tests/
├── docs/
├── reports/
├── charts/
├── requirements.txt
└── README.md
```

---

## Установка и запуск

```bash
git clone <repository-url>
cd banking-system
pip install -r requirements.txt
python src/main.py
```

---

## Функционал

- Счета: BankAccount, SavingsAccount, PremiumAccount, InvestmentAccount
- Транзакции: пополнение, снятие, переводы
- Очередь с приоритетами
- Аудит и логирование
- Анализ рисков и блокировка
- Отчёты: текст, JSON, CSV, графики

---

## Принципы ООП

- Инкапсуляция
- Наследование
- Полиморфизм
- Абстракция

---

## Лицензия

MIT