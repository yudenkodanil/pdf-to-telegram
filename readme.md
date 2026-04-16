# 📄 PDF Notification Parser

Приложение с графическим интерфейсом для быстрого извлечения и форматирования данных из **экстренных извещений** (PDF).  
Основная цель — автоматизировать рутину врача-эпидемиолога и упростить подготовку сообщений для Telegram.

---

## 🚀 Возможности

- 📑 Извлечение текста из PDF (`PyPDF2`)
- 🔍 Парсинг ключевых полей (ФИО, возраст, диагноз, даты и т.д.)
- 🎨 Автоматическое форматирование текста в **Markdown** (готово для вставки в Telegram)
- 🖱️ Поддержка **drag & drop** (перетащите файлы прямо в окно)
- 📂 Обработка **нескольких PDF одновременно**
- 📋 Быстрое копирование результата в буфер обмена
- 🖥️ Удобный интерфейс на `tkinterdnd2`

---

## 🖼️ Скриншоты

*(Добавь сюда скриншоты работы программы — окно с результатом и пример в Telegram)*

---

## 🛠️ Стек технологий

- [Python 3.9+](https://www.python.org/)  
- [PyPDF2](https://pypi.org/project/pypdf2/) — извлечение текста из PDF  
- [tkinter / tkinterdnd2](https://pypi.org/project/tkinterdnd2/) — GUI и drag&drop  
- [re (Regex)](https://docs.python.org/3/library/re.html) — парсинг текста  
- [dataclasses](https://docs.python.org/3/library/dataclasses.html) — структурирование данных  

---

## 📦 Установка

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/username/pdf-notification-parser.git
cd pdf-notification-parser

# 2. Установите зависимости
pip install -r requirements.txt
```

*(или вручную)*

```bash
pip install PyPDF2 tkinterdnd2
```

---

## 1️⃣ Создание виртуального окружения

| Платформа | Команды |
|-----------|---------|
| **Windows** | ```bash<br>cd путь/к/вашему/проекту<br>python -m venv venv``` |
| **Mac / Linux** | ```bash<br>cd путь/к/вашему/проекту<br>python3 -m venv venv``` |

## 2️⃣ Активация виртуального окружения

| Платформа | Команды |
|-----------|---------|
| **Windows Command Prompt** | ```bash<br>venv\Scripts\activate``` |
| **Windows PowerShell** | ```bash<br>.\venv\Scripts\Activate.ps1``` |
| **Mac / Linux** | ```bash<b>source venv/bin/activate``` |

> После активации вы увидите `(venv)` в начале строки терминала.

## 3️⃣ Пример активации для Windows

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---


## ▶️ Использование

```bash
python main.py
```

1. Запустите приложение  
2. Перетащите PDF или выберите его кнопкой  
3. Нажмите **«Копировать (Markdown)»**  
4. Вставьте готовый текст прямо в Telegram  

---

## 📂 Структура проекта

```
pdf-notification-parser/
├── main.py          # Основной код программы
├── readme.txt       # Документация
├── requirements.txt # Зависимости
└── examples/        # Примеры PDF для теста
```

---

## ✅ Пример результата

```markdown
‼️ Вирусный гепатит
**ФИО:** Иванов Иван Иванович, 34
**Ds:** Гепатит C
**Дата поступления ЭИ:** Э12345 от 01.09.2025
**Место работы/учебы:** ООО «Пример»
**Последнее посещение:** 30.08.2025
**Дата заболевания:** 28.08.2025
**Дата обращения:** 29.08.2025
**Госпитализация:** амбулаторное лечение
**Этиологическая расшифровка:** в работе
**Дополнительная информация:**
Жалобы на слабость, повышение температуры
```

---

## 📌 Roadmap

- [ ] Экспорт в TXT/HTML  
- [ ] Поддержка Excel-отчётов  
- [ ] Визуальные темы для интерфейса  
- [ ] Автосохранение результатов  

---

## 📦 Сборка в .exe (для Windows)
Чтобы скомпилировать программу в один исполняемый файл, который не требует установки Python:
```bash
pip install pyinstaller
pyinstaller --onefile --noconsole main.py
```

---

## 👨‍⚕️ Автор

Разработано для практических задач врача-эпидемиолога.  
Автор: [@yudenkodanil](https://t.me/yudenkodanil)

---
