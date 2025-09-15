import re
import PyPDF2
from dataclasses import dataclass, asdict
from tkinter import *
from tkinter import filedialog, messagebox, scrolledtext
from tkinterdnd2 import DND_FILES, TkinterDnD


# ------------------------- Вспомогательные функции ------------------------- #
def safe_get(match, default="-") -> str:
    return match.group(1).strip() if match else default


# ------------------------- Модель данных ------------------------- #
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


# ------------------------- Извлечение текста ------------------------- #
class PDFExtractor:
    @staticmethod
    def extract_text(pdf_path: str) -> str:
        try:
            text = ""
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    extracted = page.extract_text() or ""
                    text += extracted + "\n"
            return text
        except Exception as e:
            raise RuntimeError(f"Ошибка при чтении PDF: {e}")


# ------------------------- Парсер ------------------------- #
class PDFParser:
    PATTERNS = {
        "full_name": r"(?:Фамилия Имя Отчество|ФИО пациента)\s*[:\n]*\s*(.*?)\s*\n",
        "age": r"Пол:\s*(.*?)\s* Возраст:",
        "diagnosis": r"Дата постановки\s*диагноза\s*(.*?)\s*Диагноз",
        "diagnosis_final": r"Дата изменения\s*диагноза\s*(.*?)\s*Измененный/уточненный",
        "notification_number": r"Номер экстренного извещения\s*(Э\d+)",
        "notification_date": r"Место работы/учебы/детское учреждение:\s*дд.мм.гггг\s*(.*?)\s*Дата заполнения формы",
        "date_request": r"Дата госпитализации\s*дд.мм.гггг\s*(.*?)\s*Дата первичного обращения",
        "organization": r"Место работы/учебы/детское учреждение:\s*(.*?)\s*дд.мм.гггг",
        "last_visit": r"учреждение\s*дд.мм.гггг\s*(.*?)\s*Дата последнего посещения места работы,",
        "disease_date": r"заполнения извещения:\s*дд.мм.гггг\s*(.*?)\s*Дата заболевания",
        "hosp_date": r"Дата заболевания\s*дд.мм.гггг\s*(.*?)\s*Дата госпитализации",
        "hosp_place": r"Другое\s*(.*?)\s*Если да, название",
        "additional_info": r"Клиническая информация\s*(.*?)\s*Дополнительная информация/примечания, включая",
    }

    def __init__(self, text: str):
        self.text = text

    def parse(self) -> NotificationData:
        data = NotificationData()
        for field, pattern in self.PATTERNS.items():
            match = re.search(pattern, self.text, re.DOTALL | re.MULTILINE)
            value = safe_get(match)
            setattr(data, field, value)

        # Убираем лишние переносы
        data.additional_info = (
            data.additional_info.replace("\n", " ").replace("  ", " ").strip()
        )

        # Если нет уточненного диагноза — берём основной
        if not data.diagnosis_final or data.diagnosis_final == "-":
            data.diagnosis_final = data.diagnosis

        return data


# ------------------------- Форматирование ------------------------- #
class NotificationFormatter:
    TEMPLATE = """‼️ {diagnosis}
ФИО: {full_name}, {age}
Ds: {diagnosis_final}
Дата поступления ЭИ: {notification_number} от {notification_date}
Место работы/учебы: {organization}
Последнее посещение: {last_visit}
Дата заболевания: {disease_date}
Дата обращения: {date_request}
Госпитализация: {hosp}
Этиологическая расшифровка: в работе
Дополнительная информация:
{additional_info}"""

    @staticmethod
    def format(data: NotificationData) -> str:
        hosp_str = (
            f"{data.hosp_date} в {data.hosp_place}"
            if data.hosp_date != "-" and data.hosp_place != "-"
            else "амбулаторное лечение"
        )

        return NotificationFormatter.TEMPLATE.format(
            **asdict(data), hosp=hosp_str
        )


# ------------------------- GUI ------------------------- #
class NotificationApp:
    def __init__(self, root):
        self.root = root
        self.output_text = None
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Обработка экстренных извещений для Telegram (@yudenkodanil)")
        self.root.geometry("900x700")

        Label(
            self.root, text="Перетащите PDF файл сюда или нажмите кнопку ниже", font=("Arial", 12)
        ).pack(pady=10)

        browse_btn = Label(
            self.root,
            text="Выбрать файл",
            relief="raised",
            padx=10,
            pady=5,
            cursor="hand2",
        )
        browse_btn.pack(pady=5)
        browse_btn.bind("<Button-1>", lambda e: self.browse_file())
        browse_btn.drop_target_register(DND_FILES)
        browse_btn.dnd_bind("<<Drop>>", self.handle_drop)

        Label(self.root, text="Результат:", font=("Arial", 12)).pack(pady=10)

        self.output_text = scrolledtext.ScrolledText(
            self.root, width=100, height=30, font=("Courier New", 10)
        )
        self.output_text.pack(pady=10, padx=10)
        self.output_text.drop_target_register(DND_FILES)
        self.output_text.dnd_bind("<<Drop>>", self.handle_drop)

        Button(self.root, text="Копировать результат", command=self.copy_text).pack(pady=5)

        # горячие клавиши
        self.output_text.bind("<Control-c>", self.copy_text)
        self.output_text.bind("<Command-c>", self.copy_text)  # macOS

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.handle_drop)

    def copy_text(self, event=None):
        text = self.output_text.get(1.0, END).replace("\n\n", "\n").strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)

    def process_file(self, file_path: str):
        try:
            text = PDFExtractor.extract_text(file_path)
            if not text:
                messagebox.showerror("Ошибка", "Не удалось извлечь текст из PDF")
                return

            parser = PDFParser(text)
            data = parser.parse()

            output = NotificationFormatter.format(data)
            self.output_text.delete(1.0, END)
            self.output_text.insert(END, output)

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def handle_drop(self, event):
        file_path = event.data.strip("{}")
        if file_path.lower().endswith(".pdf"):
            self.process_file(file_path)
        else:
            messagebox.showerror("Ошибка", "Пожалуйста, перетащите PDF файл")

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.process_file(file_path)


# ------------------------- Запуск ------------------------- #
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = NotificationApp(root)
    root.mainloop()
