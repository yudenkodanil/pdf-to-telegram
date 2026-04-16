import re
import PyPDF2
from dataclasses import dataclass
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinterdnd2 import DND_FILES, TkinterDnD

# ======== Словарь сокращений организаций =========
REPLACEMENTS = {
    "МУНИЦИПАЛЬНОЕ АВТОНОМНОЕ ОБЩЕОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ": "МАОУ",
    "Государственное автономное учреждение здравоохранения Амурской области": "ГАУЗ АО",
    "Государственное автономное учреждение здравоохранения": "ГАУЗ",
    "Федеральное бюджетное учреждение здравоохранения": "ФБУЗ",
    "Государственное бюджетное учреждение здравоохранения Амурской области": "ГБУЗ АО",
    "Государственное бюджетное учреждение здравоохранения": "ГБУЗ",
    "МУНИЦИПАЛЬНОЕ АВТОНОМНОЕ ДОШКОЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ": "МАДОУ",
    "ДЕТСКИЙ САД": "ДС",
    "Амурская областная инфекционная больница": "АОИБ",
    "Амурская областная детская клиническая больница": "АОДКБ",
    "Детская городская клиническая больница": "ДГКБ",
    "ГОРОДА БЛАГОВЕЩЕНСКА": "г.Благовещенска",
    "Благовещенская городская клиническая больница" : "БГКБ"
}

def safe_get(match, default="-"):
    return match.group(1).strip() if match else default

def replace_institutions(text: str) -> str:
    """Заменяем длинные названия организаций на сокращения"""
    for long, short in REPLACEMENTS.items():
        text = re.sub(re.escape(long), short, text, flags=re.IGNORECASE)
    return text

# ======== Дата класс для уведомления =========
@dataclass
class NotificationData:
    full_name: str = "-"
    age: str = "-"
    diagnosis: str = "-"
    diagnosis_final: str = "-"
    notification_number: str = "-"
    notification_date: str = "-"
    date_request: str = "-"
    organization: str = "-"
    last_visit: str = "-"
    disease_date: str = "-"
    hosp_date: str = "-"
    hosp_place: str = "-"
    additional_info: str = "-"

    def to_md(self) -> str:
        hosp = f"{self.hosp_date} в {self.hosp_place}" if self.hosp_date and self.hosp_place else "амбулаторное лечение"
        return f"""‼️ **{self.diagnosis}**
**ФИО:** {self.full_name}, {self.age}
**Ds:** {self.diagnosis_final}
**Дата поступления ЭИ:** {self.notification_number} от {self.notification_date}
**Место работы/учебы:** {self.organization}
**Последнее посещение:** {self.last_visit}
**Дата заболевания:** {self.disease_date}
**Дата обращения:** {self.date_request}
**Госпитализация:** {hosp}
**Этиологическая расшифровка:** в работе
**Дополнительная информация:**
{self.additional_info}"""

    def to_plain(self) -> str:
        hosp = f"{self.hosp_date} в {self.hosp_place}" if self.hosp_date and self.hosp_place else "амбулаторное лечение"
        return f"""‼️ {self.diagnosis}
ФИО: {self.full_name}, {self.age}
Ds: {self.diagnosis_final}
Дата поступления ЭИ: {self.notification_number} от {self.notification_date}
Место работы/учебы: {self.organization}
Последнее посещение: {self.last_visit}
Дата заболевания: {self.disease_date}
Дата обращения: {self.date_request}
Госпитализация: {hosp}
Этиологическая расшифровка: в работе
Дополнительная информация:
{self.additional_info}"""

# ======== Извлечение текста из PDF =========
class PDFExtractor:
    @staticmethod
    def extract_text(pdf_path: str) -> str:
        text = ""
        try:
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() or ""
        except Exception:
            return ""
        return text

# ======== Парсер PDF =========
class PDFParser:
    # Предкомпилируем регулярные выражения
    PATTERNS = {
        "full_name": re.compile(r"(?:Фамилия Имя Отчество|ФИО пациента)\s*[\n:]*\s*(.*?)\s*\n", re.DOTALL),
        "age": re.compile(r"Пол:\s*(.*?)\s* Возраст:", re.DOTALL),
        "diagnosis": re.compile(r"Дата постановки\s*диагноза\s*(.*?)\s*Диагноз", re.DOTALL),
        "diagnosis_final": re.compile(r"Дата изменения\s*диагноза\s*(.*?)\s*Измененный/уточненный", re.DOTALL),
        "notification_number": re.compile(r"Номер экстренного извещения\s*(Э\d+)", re.DOTALL),
        "notification_date": re.compile(r"Место работы/учебы/детское учреждение:\s*дд.мм.гггг\s*(.*?)\s*Дата заполнения формы", re.DOTALL),
        "date_request": re.compile(r"Дата госпитализации\s*дд.мм.гггг\s*(.*?)\s*Дата первичного обращения", re.DOTALL),
        "last_visit": re.compile(r"учреждение\s*дд.мм.гггг\s*(.*?)\s*Дата последнего посещения места работы,", re.DOTALL),
        "disease_date": re.compile(r"заполнения извещения:\s*дд.мм.гггг\s*(.*?)\s*Дата заболевания", re.DOTALL),
        "hosp_date": re.compile(r"Дата заболевания\s*дд.мм.гггг\s*(.*?)\s*Дата госпитализации", re.DOTALL),
        "hosp_place": re.compile(r"Другое\s*(.*?)\s*Если да, название", re.DOTALL),
        "additional_info": re.compile(r"Клиническая информация\s*(.*?)\s*Дополнительная информация/примечания, включая", re.DOTALL),
        "organization_alt": re.compile(r"Адрес фактического места жительства:(.*?)Место работы/учебы/детское", re.DOTALL),
        "social_organization": re.compile(r"Класс \(группа\)\s*(.*?)\s*Социально-значимое", re.DOTALL),
    }

    def __init__(self, text: str):
        self.text = text

    def clean_value(self, value: str) -> str:
        """Удаляет переносы строк и лишние пробелы внутри текста"""
        if not value or value == "-":
            return "-"
        # Заменяем все виды пробельных символов (включая \n) на обычный пробел
        cleaned = re.sub(r'\s+', ' ', value)
        return cleaned.strip()

    def parse(self) -> NotificationData:
        data = {}
        for key in ["full_name","age","diagnosis","diagnosis_final","notification_number",
                    "notification_date","date_request","last_visit","disease_date","hosp_date",
                    "hosp_place","additional_info"]:
            match = self.PATTERNS[key].search(self.text)
            raw_value = safe_get(match)
            
            # Применяем очистку ко всем полям
            data[key] = self.clean_value(raw_value)

        # Дополнительная обработка диагноза
        if not data["diagnosis_final"] or data["diagnosis_final"] == "-":
            data["diagnosis_final"] = data["diagnosis"]

        # Логика места работы/учёбы
        org_match = self.PATTERNS["organization_alt"].search(self.text)
        org_value = self.clean_value(safe_get(org_match))
        
        if org_value == "-":
            social_match = self.PATTERNS["social_organization"].search(self.text)
            org_value = self.clean_value(safe_get(social_match))
            
        # Применяем замену названий (сокращения) к организации и месту госпитализации
        data["organization"] = replace_institutions(org_value)
        data["hosp_place"] = replace_institutions(data["hosp_place"])
        
        return NotificationData(**data)

# ======== Сервис обработки PDF =========
class PDFService:
    @staticmethod
    def process(pdf_paths: list[str]) -> list[NotificationData]:
        results = []
        for path in pdf_paths:
            text = PDFExtractor.extract_text(path)
            if not text:
                continue
            # Добавлена защита от сбоев при парсинге отдельного файла
            try:
                results.append(PDFParser(text).parse())
            except Exception as e:
                print(f"Ошибка при обработке файла {path}: {e}")
        return results

# ======== GUI =========
class NotificationApp:
    def __init__(self, root):
        self.root = root
        self.output_text = None
        self.data_blocks = []  # Список для хранения распарсенных объектов
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Обработка экстренных извещений (@yudenkodanil)")
        self.root.geometry("800x750")

        tk.Label(self.root, text="Перетащите PDF или выберите файлы", font=("Arial", 12)).pack(pady=10)
        
        browse_btn = tk.Label(self.root, text="Выбрать файлы", relief="raised", padx=10, pady=5, cursor="hand2")
        browse_btn.pack(pady=5)
        browse_btn.bind("<Button-1>", lambda e: self.select_files())
        browse_btn.drop_target_register(DND_FILES)
        browse_btn.dnd_bind("<<Drop>>", self.handle_drop)

        tk.Label(self.root, text="Результат:", font=("Arial", 12)).pack(pady=10)
        
        self.output_text = scrolledtext.ScrolledText(self.root, width=100, height=35, font=("Courier New", 10))
        self.output_text.pack(pady=10, padx=10)
        self.output_text.drop_target_register(DND_FILES)
        self.output_text.dnd_bind("<<Drop>>", self.handle_drop)

        # Теги для подсветки текста в окне
        self.output_text.tag_config("header", foreground="blue", font=("Courier New", 10, "bold"))
        self.output_text.tag_config("diagnosis", foreground="red", font=("Courier New", 10, "bold"))

        # Фрейм для кнопок
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Копировать для Telegram", 
                  command=lambda: self.copy_data(use_markdown=True), bg="#e1f5fe").pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="Копировать для MAX", 
                  command=lambda: self.copy_data(use_markdown=False), bg="#fbcff6").pack(side=tk.LEFT, padx=10)

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.handle_drop)

    def select_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        self.process_files(file_paths)

    def handle_drop(self, event):
        file_paths = self.root.tk.splitlist(event.data)
        pdfs = [f.strip("{}") for f in file_paths if f.lower().endswith(".pdf")]
        self.process_files(pdfs)

    def process_files(self, file_paths: list[str]):
        if not file_paths:
            messagebox.showerror("Ошибка", "Нет выбранных PDF файлов")
            return
        
        self.data_blocks.clear()
        self.output_text.delete(1.0, tk.END)
        
        for data in PDFService.process(file_paths):
            self.data_blocks.append(data)
            self.display_clean(data)

    def display_clean(self, data: NotificationData):
        """Отображение данных в UI для просмотра"""
        self.output_text.insert(tk.END, data.diagnosis + "\n", "diagnosis")
        fields = [
            ("ФИО", f"{data.full_name}, {data.age}"),
            ("Ds", data.diagnosis_final),
            ("Дата поступления ЭИ", f"{data.notification_number} от {data.notification_date}"),
            ("Место работы/учебы", data.organization),
            ("Последнее посещение", data.last_visit),
            ("Дата заболевания", data.disease_date),
            ("Дата обращения", data.date_request),
            ("Госпитализация", f"{data.hosp_date} в {data.hosp_place}" if data.hosp_date and data.hosp_place else "амбулаторное лечение"),
            ("Этиологическая расшифровка", "в работе"),
            ("Дополнительная информация", data.additional_info),
        ]
        
        for title, value in fields:
            self.output_text.insert(tk.END, title + ": ", "header")
            self.output_text.insert(tk.END, value + "\n")
        self.output_text.insert(tk.END, "\n")

    def copy_data(self, use_markdown: bool):
        """Прямое копирование данных из объектов (без парсинга текстового окна)"""
        if not self.data_blocks:
            messagebox.showwarning("Внимание", "Нет данных для копирования")
            return

        if use_markdown:
            texts = [data.to_md() for data in self.data_blocks]
            msg = "Текст скопирован в буфер обмена для Telegram"
        else:
            texts = [data.to_plain() for data in self.data_blocks]
            msg = "Текст скопирован в буфер обмена для MAX"

        final_text = "\n\n---\n\n".join(texts)
        self.root.clipboard_clear()
        self.root.clipboard_append(final_text)
        messagebox.showinfo("Готово", msg)

# ======== Главный запуск =========
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = NotificationApp(root)
    root.mainloop()
