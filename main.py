import re
import PyPDF2
from dataclasses import dataclass
from tkinter import *
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
        return f"""‼️ {self.diagnosis}
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

# ======== Парсер PDF с новой логикой места работы/учёбы =========
class PDFParser:
    PATTERNS = {
        "full_name": r"(?:Фамилия Имя Отчество|ФИО пациента)\s*[\n:]*\s*(.*?)\s*\n",
        "age": r"Пол:\s*(.*?)\s* Возраст:",
        "diagnosis": r"Дата постановки\s*диагноза\s*(.*?)\s*Диагноз",
        "diagnosis_final": r"Дата изменения\s*диагноза\s*(.*?)\s*Измененный/уточненный",
        "notification_number": r"Номер экстренного извещения\s*(Э\d+)",
        "notification_date": r"Место работы/учебы/детское учреждение:\s*дд.мм.гггг\s*(.*?)\s*Дата заполнения формы",
        "date_request": r"Дата госпитализации\s*дд.мм.гггг\s*(.*?)\s*Дата первичного обращения",
        "last_visit": r"учреждение\s*дд.мм.гггг\s*(.*?)\s*Дата последнего посещения места работы,",
        "disease_date": r"заполнения извещения:\s*дд.мм.гггг\s*(.*?)\s*Дата заболевания",
        "hosp_date": r"Дата заболевания\s*дд.мм.гггг\s*(.*?)\s*Дата госпитализации",
        "hosp_place": r"Другое\s*(.*?)\s*Если да, название",
        "additional_info": r"Клиническая информация\s*(.*?)\s*Дополнительная информация/примечания, включая",
        # Новая логика места работы/учёбы
        "organization_alt": r'Адрес фактического места жительства:(.*?)Место работы/учебы/детское',
        "social_organization": r"Класс \(группа\)\s*(.*?)\s*Социально-значимое",
    }

    def __init__(self, text: str):
        self.text = text

    def parse(self) -> NotificationData:
        data = {}
        # Основные поля
        for key in ["full_name","age","diagnosis","diagnosis_final","notification_number",
                    "notification_date","date_request","last_visit","disease_date","hosp_date",
                    "hosp_place","additional_info"]:
            match = re.search(self.PATTERNS[key], self.text, re.DOTALL)
            value = safe_get(match)
            if key in ["additional_info"]:
                value = value.replace("\n"," ").replace("  "," ").strip()
            data[key] = value

        if not data["diagnosis_final"]:
            data["diagnosis_final"] = data["diagnosis"]

        # Новая логика места работы/учёбы
        org_match = re.search(self.PATTERNS["organization_alt"], self.text, re.DOTALL)
        org_value = safe_get(org_match)
        org_value = replace_institutions(org_value.replace("\n"," ").strip())
        if not org_value:
            social_match = re.search(self.PATTERNS["social_organization"], self.text, re.DOTALL)
            org_value = replace_institutions(safe_get(social_match).replace("\n"," ").strip())
        data["organization"] = org_value if org_value else "-"

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
            results.append(PDFParser(text).parse())
        return results

# ======== GUI =========
class NotificationApp:
    def __init__(self, root):
        self.root = root
        self.output_text = None
        self.data_blocks = []
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Обработка экстренных извещений (@yudenkodanil)")
        self.root.geometry("800x750")

        Label(self.root, text="Перетащите PDF или выберите файлы", font=("Arial", 12)).pack(pady=10)

        browse_btn = Label(self.root, text="Выбрать файлы", relief="raised", padx=10, pady=5, cursor="hand2")
        browse_btn.pack(pady=5)
        browse_btn.bind("<Button-1>", lambda e: self.select_files())
        browse_btn.drop_target_register(DND_FILES)
        browse_btn.dnd_bind("<<Drop>>", self.handle_drop)

        Label(self.root, text="Результат:", font=("Arial", 12)).pack(pady=10)

        self.output_text = scrolledtext.ScrolledText(self.root, width=100, height=35, font=("Courier New", 10))
        self.output_text.pack(pady=10, padx=10)
        self.output_text.drop_target_register(DND_FILES)
        self.output_text.dnd_bind("<<Drop>>", self.handle_drop)

        self.output_text.tag_config("header", foreground="blue", font=("Courier New", 10, "bold"))
        self.output_text.tag_config("diagnosis", foreground="red", font=("Courier New", 10, "bold"))

        Button(self.root, text="Копировать Markdown", command=self.copy_md).pack(pady=5)

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
        self.output_text.delete(1.0, END)

        for data in PDFService.process(file_paths):
            self.data_blocks.append(data)
            self.display_clean(data)

    def display_clean(self, data: NotificationData):
        self.output_text.insert(END, data.diagnosis + "\n", "diagnosis")

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
            self.output_text.insert(END, title + ": ", "header")
            self.output_text.insert(END, value + "\n")

        self.output_text.insert(END, "\n")

    def copy_md(self):
        current_text = self.output_text.get(1.0, END).strip()
        if not current_text:
            messagebox.showwarning("Внимание", "Нет текста для копирования")
            return

        md_lines = []
        lines = current_text.splitlines()
        in_diagnosis = False
        diagnosis_lines = []

        for i, line in enumerate(lines):
            line_strip = line.strip()
            if not line_strip:
                if in_diagnosis:
                    md_lines.append(f"‼️ **{' '.join(diagnosis_lines)}**")
                    diagnosis_lines.clear()
                    in_diagnosis = False
                md_lines.append("")
                continue

            idx_start = f"{i + 1}.0"
            tags = self.output_text.tag_names(idx_start)

            if "diagnosis" in tags:
                if not in_diagnosis:
                    in_diagnosis = True
                diagnosis_lines.append(line_strip)
                continue
            else:
                if in_diagnosis:
                    md_lines.append(f"‼️ **{' '.join(diagnosis_lines)}**")
                    diagnosis_lines.clear()
                    in_diagnosis = False

            if ":" in line_strip:
                key, value = line_strip.split(":", 1)
                md_lines.append(f"**{key.strip()}:**{value}")
            else:
                md_lines.append(line_strip)

        if in_diagnosis and diagnosis_lines:
            md_lines.append(f"‼️ **{' '.join(diagnosis_lines)}**")

        md_text = "\n".join(md_lines)
        self.root.clipboard_clear()
        self.root.clipboard_append(md_text)
        messagebox.showinfo("Готово", "Текст скопирован в буфер обмена с Markdown")

# ======== Главный запуск =========
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = NotificationApp(root)
    root.mainloop()
