import re
import PyPDF2
from dataclasses import dataclass
from tkinter import *
from tkinter import filedialog, messagebox, scrolledtext
from tkinterdnd2 import DND_FILES, TkinterDnD


def safe_get(match, default="-"):
    return match.group(1).strip() if match else default


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


class PDFExtractor:
    @staticmethod
    def extract_text(pdf_path: str) -> str:
        text = ""
        try:
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    text += page_text + "\n"
        except Exception as e:
            print(f"Ошибка чтения PDF: {e}")
        return text


class PDFParser:
    PATTERNS = {
        "full_name": r"(?:Фамилия Имя Отчество|ФИО пациента)\s*[\n:]*\s*(.*?)\s*\n",
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
        data = {}
        for key, pattern in self.PATTERNS.items():
            value = safe_get(re.search(pattern, self.text, re.DOTALL))
            if key == "additional_info":
                value = value.replace("\n", " ").replace("  ", " ").strip()
            data[key] = value

        if not data["diagnosis_final"]:
            data["diagnosis_final"] = data["diagnosis"]

        return NotificationData(**data)


class NotificationFormatter:
    TEMPLATE_MD = """‼️ {diagnosis}
**ФИО:** {full_name}, {age}
**Ds:** {diagnosis_final}
**Дата поступления ЭИ:** {notification_number} от {notification_date}
**Место работы/учебы:** {organization}
**Последнее посещение:** {last_visit}
**Дата заболевания:** {disease_date}
**Дата обращения:** {date_request}
**Госпитализация:** {hosp}
**Этиологическая расшифровка:** в работе
**Дополнительная информация:**
{additional_info}"""

    TEMPLATE_HTML = """‼️ {diagnosis}<br>
<b>ФИО:</b> {full_name}, {age}<br>
<b>Ds:</b> {diagnosis_final}<br>
<b>Дата поступления ЭИ:</b> {notification_number} от {notification_date}<br>
<b>Место работы/учебы:</b> {organization}<br>
<b>Последнее посещение:</b> {last_visit}<br>
<b>Дата заболевания:</b> {disease_date}<br>
<b>Дата обращения:</b> {date_request}<br>
<b>Госпитализация:</b> {hosp}<br>
<b>Этиологическая расшифровка:</b> в работе<br>
<b>Дополнительная информация:</b><br>
{additional_info}"""

    @staticmethod
    def format_md(data: NotificationData) -> str:
        hosp = (
            f"{data.hosp_date} в {data.hosp_place}"
            if data.hosp_date and data.hosp_place else "амбулаторное лечение"
        )
        return NotificationFormatter.TEMPLATE_MD.format(**data.__dict__, hosp=hosp)

    @staticmethod
    def format_html(data: NotificationData) -> str:
        hosp = (
            f"{data.hosp_date} в {data.hosp_place}"
            if data.hosp_date and data.hosp_place else "амбулаторное лечение"
        )
        return NotificationFormatter.TEMPLATE_HTML.format(**data.__dict__, hosp=hosp)


class NotificationApp:
    def __init__(self, root):
        self.root = root
        self.output_text = None
        self.data_blocks = []
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Обработка экстренных извещений (@yudenkodanil)")
        self.root.geometry("900x750")

        Label(self.root, text="Перетащите PDF или нажмите кнопку", font=("Arial", 12)).pack(pady=10)

        browse_btn = Label(
            self.root, text="Выбрать файлы", relief="raised", padx=10, pady=5, cursor="hand2"
        )
        browse_btn.pack(pady=5)
        browse_btn.bind("<Button-1>", lambda e: self.browse_file())
        browse_btn.drop_target_register(DND_FILES)
        browse_btn.dnd_bind("<<Drop>>", self.handle_drop)

        Label(self.root, text="Результат:", font=("Arial", 12)).pack(pady=10)

        self.output_text = scrolledtext.ScrolledText(
            self.root, width=100, height=35, font=("Courier New", 10)
        )
        self.output_text.pack(pady=10, padx=10)
        self.output_text.drop_target_register(DND_FILES)
        self.output_text.dnd_bind("<<Drop>>", self.handle_drop)

        Button(self.root, text="Копировать (Markdown)", command=self.copy_text_md).pack(pady=5)
        Button(self.root, text="Копировать (HTML)", command=self.copy_text_html).pack(pady=5)

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.handle_drop)

    def copy_text_md(self):
        self._copy_to_clipboard("\n\n".join(block["md"] for block in self.data_blocks))

    def copy_text_html(self):
        self._copy_to_clipboard("<hr>".join(block["html"] for block in self.data_blocks))

    def _copy_to_clipboard(self, text: str):
        self.root.clipboard_clear()
        self.root.clipboard_append(text.strip())
        messagebox.showinfo("Готово", "Текст скопирован в буфер обмена")

    def process_files(self, file_paths: list[str]):
        self.data_blocks.clear()
        outputs = []
        for file_path in file_paths:
            text = PDFExtractor.extract_text(file_path)
            if not text:
                messagebox.showerror("Ошибка", f"Не удалось извлечь текст из {file_path}")
                continue

            parser = PDFParser(text)
            data = parser.parse()

            md_output = NotificationFormatter.format_md(data)
            html_output = NotificationFormatter.format_html(data)
            self.data_blocks.append({"md": md_output, "html": html_output})

            outputs.append(md_output)

        self.output_text.delete(1.0, END)
        self.output_text.insert(END, "\n\n".join(outputs))

    def handle_drop(self, event):
        file_paths = self.root.tk.splitlist(event.data)
        pdfs = [f.strip("{}") for f in file_paths if f.lower().endswith(".pdf")]
        if pdfs:
            self.process_files(pdfs)
        else:
            messagebox.showerror("Ошибка", "Пожалуйста, перетащите PDF файл")

    def browse_file(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        if file_paths:
            self.process_files(file_paths)


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = NotificationApp(root)
    root.mainloop()