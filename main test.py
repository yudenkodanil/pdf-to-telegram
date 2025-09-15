import re
import PyPDF2
from tkinter import *
from tkinter import filedialog, messagebox, scrolledtext
from tkinterdnd2 import DND_FILES, TkinterDnD


def safe_get(match, default="-"):
    """Безопасное извлечение значения из regex match."""
    return match.group(1).strip() if match else default


class PDFExtractor:
    """Извлечение текста из PDF."""

    @staticmethod
    def extract_text(pdf_path: str) -> str:
        text = ""
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
        return text


class PDFParser:
    """Парсинг текста из экстренного извещения."""

    def __init__(self, text: str):
        self.text = text
        self.data = {}

    def parse(self) -> dict:
        self.data = {
            "full_name": safe_get(
                re.search(r"(?:Фамилия Имя Отчество|ФИО пациента)\s*[\n:]*\s*(.*?)\s*\n", self.text)
            ),
            "age": safe_get(re.search(r"Пол:\s*(.*?)\s* Возраст:", self.text)),
            "diagnosis": safe_get(
                re.search(r"Дата постановки\s*диагноза\s*(.*?)\s*Диагноз", self.text, re.DOTALL)
            ),
            "diagnosis_final": safe_get(
                re.search(r"Дата изменения\s*диагноза\s*(.*?)\s*Измененный/уточненный", self.text, re.DOTALL)
            ),
            "notification_number": safe_get(
                re.search(r"Номер экстренного извещения\s*(Э\d+)", self.text)
            ),
            # Дата подачи ЭИ
            "notification_date": safe_get(
                re.search(
                    r"Место работы/учебы/детское учреждение:\s*дд.мм.гггг\s*(.*?)\s*Дата заполнения формы",
                    self.text,
                    re.DOTALL,
                )
            ),
            # Дата обращения
            "date_request": safe_get(
                re.search(
                    r"Дата госпитализации\s*дд.мм.гггг\s*(.*?)\s*Дата первичного обращения",
                    self.text,
                    re.DOTALL,
                )
            ),
            "organization": safe_get(
                re.search(
                    r"Место работы/учебы/детское учреждение:\s*(.*?)\s*дд.мм.гггг",
                    self.text,
                    re.DOTALL,
                )
            ),
            "last_visit": safe_get(
                re.search(
                    r"учреждение\s*дд.мм.гггг\s*(.*?)\s*Дата последнего посещения места работы,",
                    self.text,
                    re.DOTALL,
                )
            ),
            "disease_date": safe_get(
                re.search(
                    r"заполнения извещения:\s*дд.мм.гггг\s*(.*?)\s*Дата заболевания",
                    self.text,
                    re.DOTALL,
                )
            ),
            "hosp_date": safe_get(
                re.search(
                    r"Дата заболевания\s*дд.мм.гггг\s*(.*?)\s*Дата госпитализации",
                    self.text,
                    re.DOTALL,
                )
            ),
            "hosp_place": safe_get(
                re.search(r"Другое\s*(.*?)\s*Если да, название", self.text, re.DOTALL)
            ),
            "additional_info": safe_get(
                re.search(
                    r"Клиническая информация\s*(.*?)\s*Дополнительная информация/примечания, включая",
                    self.text,
                    re.DOTALL,
                )
            ).replace("\n", " ").replace("  ", " ").strip(),
        }

        # если нет уточнённого диагноза — используем основной
        if not self.data["diagnosis_final"]:
            self.data["diagnosis_final"] = self.data["diagnosis"]

        return self.data


class NotificationFormatter:
    """Форматирование данных для вывода."""

    @staticmethod
    def format(data: dict) -> str:
        lines = [
            f"‼️ {data['diagnosis']}",
            f"ФИО: {data['full_name']}, {data['age']}",
            f"Ds: {data['diagnosis_final']}",
            f"Дата поступления ЭИ: {data['notification_number']} от {data['notification_date']}",
            f"Место работы/учебы: {data['organization']}",
            f"Последнее посещение: {data['last_visit']}",
            f"Дата заболевания: {data['disease_date']}",
            f"Дата обращения: {data['date_request']}",
            f"Госпитализация: {data['hosp_date']} в {data['hosp_place']}"
            if data["hosp_date"] and data["hosp_place"]
            else "Госпитализация: амбулаторное лечение",
            "Этиологическая расшифровка: в работе",
            "Дополнительная информация:",
            data["additional_info"],
        ]
        return "\n".join(lines)


class NotificationApp:
    """GUI-приложение для обработки ЭИ."""

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
        """Копирование текста в буфер обмена."""
        self.root.clipboard_clear()
        text = self.output_text.get(1.0, END).replace("\n\n", "\n").strip()
        self.root.clipboard_append(text)

    def process_file(self, file_path: str):
        """Обработка выбранного файла."""
        text = PDFExtractor.extract_text(file_path)
        if not text:
            messagebox.showerror("Ошибка", "Не удалось извлечь текст из PDF")
            return

        parser = PDFParser(text)
        data = parser.parse()

        output = NotificationFormatter.format(data)
        self.output_text.delete(1.0, END)
        self.output_text.insert(END, output)

    def handle_drop(self, event):
        """Обработка drag & drop."""
        file_path = event.data.strip("{}")
        if file_path.lower().endswith(".pdf"):
            self.process_file(file_path)
        else:
            messagebox.showerror("Ошибка", "Пожалуйста, перетащите PDF файл")

    def browse_file(self):
        """Выбор файла через диалог."""
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.process_file(file_path)


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = NotificationApp(root)
    root.mainloop()