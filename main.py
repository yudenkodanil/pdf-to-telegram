import re
import PyPDF2
from dataclasses import dataclass
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkinterdnd2 import DND_FILES, TkinterDnD
import win32clipboard

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
    "Благовещенская городская клиническая больница" : "БГКБ",
    "Амурская областная клиническая больница": "АОКБ",
    "ГОСУДАРСТВЕННОЕ ПРОФЕССИОНАЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ АВТОНОМНОЕ УЧРЕЖДЕНИЕ АМУРСКОЙ ОБЛАСТИ": "ГПО АУ АО",
    "АМУРСКИЙ КОЛЛЕДЖ СТРОИТЕЛЬСТВА И ЖИЛИЩНО- КОММУНАЛЬНОГО ХОЗЯЙСТВА": "Колледж ЖКХ",
    "ГОСУДАРСТВЕННОЕ АВТОНОМНОЕ УЧРЕЖДЕНИЕ АМУРСКОЙ ОБЛАСТИ ПРОФЕССИОНАЛЬНАЯ ОБРАЗОВАТЕЛЬНАЯ ОРГАНИЗАЦИЯ": "ГАУ АО ПОО", 
    "АМУРСКИЙ МЕДИЦИНСКИЙ КОЛЛЕДЖ": "Медицинский колледж",
    "МУНИЦИПАЛЬНОЕ АВТОНОМНОЕ ДОШКОЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ": "МАДОУ",
    "МУНИЦИПАЛЬНОЕ ДОШКОЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ": "МДОБУ",
    "МУНИЦИПАЛЬНОЕ ДОШКОЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ АВТОНОМНОЕ УЧРЕЖДЕНИЕ": "МДОАУ",
    "МУНИЦИПАЛЬНОЕ ОБЩЕОБРАЗОВАТЕЛЬНОЕ АВТОНОМНОЕ УЧРЕЖДЕНИЕ": "МОАУ",
    "МУНИЦИПАЛЬНОЕ БЮДЖЕТНОЕ ОБЩЕОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ": "МБОУ",
    "МУНИЦИПАЛЬНОЕ ОБЩЕОБРАЗОВАТЕЛЬНОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ": "МОБУ",
    "МУНИЦИПАЛЬНОЕ ОБЩЕОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ": "МОУ",
    "МУНИЦИПАЛЬНОЕ ДОШКОЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ": "МДОУ",
    "МУНИЦИПАЛЬНОЕ АВТОНОМНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ ДОПОЛНИТЕЛЬНОГО ОБРАЗОВАНИЯ": "МАОУ ДО",
    "МУНИЦИПАЛЬНОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ ДОПОЛНИТЕЛЬНОГО ОБРАЗОВАНИЯ": "МБУДО",
    "МУНИЦИПАЛЬНОЕ БЮДЖЕТНОЕ ДОШКОЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ": "МБДОУ",
    "МУНИЦИПАЛЬНОЕ ОБЩЕОБРАЗОВАТЕЛЬНОЕ КАЗЁННОЕ УЧРЕЖДЕНИЕ": "МОКУ",
    "МУНИЦИПАЛЬНОЕ ОБЩЕОБРАЗОВАТЕЛЬНОЕ КАЗЕННОЕ УЧРЕЖДЕНИЕ": "МОКУ",
    "ФЕДЕРАЛЬНОЕ ГОСУДАРСТВЕННОЕ БЮДЖЕТНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ ВЫСШЕГО ОБРАЗОВАНИЯ": "ФГБОУ ВО",
    "ФЕДЕРАЛЬНОЕ ГОСУДАРСТВЕННОЕ ОБРАЗОВАТЕЛЬНОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ ВЫСШЕГО ОБРАЗОВАНИЯ": "ФГОБУ ВО",
    "ГОСУДАРСТВЕННОЕ АВТОНОМНОЕ УЧРЕЖДЕНИЕ АМУРСКОЙ ОБЛАСТИ ПРОФЕССИОНАЛЬНАЯ ОБРАЗОВАТЕЛЬНАЯ ОРГАНИЗАЦИЯ": "ГАУ АО ПОО",
    "ГОСУДАРСТВЕННОЕ ПРОФЕССИОНАЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ АВТОНОМНОЕ УЧРЕЖДЕНИЕ АМУРСКОЙ ОБЛАСТИ": "ГПОАУ АО",
    "ГОСУДАРСТВЕННОЕ ПРОФЕССИОНАЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ АМУРСКОЙ ОБЛАСТИ": "ГПОБУ АО",
    "ГОСУДАРСТВЕННОЕ АВТОНОМНОЕ ОБЩЕОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ АМУРСКОЙ ОБЛАСТИ": "ГАОУ АО",
    "ГОСУДАРСТВЕННОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ АМУРСКОЙ ОБЛАСТИ": "ГБУ АО",
    "ГОСУДАРСТВЕННОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ ЗДРАВООХРАНЕНИЯ АМУРСКОЙ ОБЛАСТИ": "ГБУЗ АО",
    "ГОСУДАРСТВЕННОЕ АВТОНОМНОЕ УЧРЕЖДЕНИЕ ЗДРАВООХРАНЕНИЯ АМУРСКОЙ ОБЛАСТИ": "ГАУЗ АО",
    "ГОСУДАРСТВЕННОЕ АВТОНОМНОЕ УЧРЕЖДЕНИЕ АМУРСКОЙ ОБЛАСТИ": "ГАУ АО",
    "ЧАСТНОЕ УЧРЕЖДЕНИЕ ДОШКОЛЬНАЯ ОБРАЗОВАТЕЛЬНАЯ ОРГАНИЗАЦИЯ": "ЧУДОО",
    "ЧАСТНОЕ ДОШКОЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ": "ЧДОУ",
    "ЧАСТНОЕ ОБЩЕОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ": "ЧОУ",
    "Частный детский сад": "ЧДС",
    "ФЕДЕРАЛЬНОЕ ГОСУДАРСТВЕННОЕ КАЗЕННОЕ УЧРЕЖДЕНИЕ": "ФГКУ",
    "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ": "ООО",
    "АКЦИОНЕРНОЕ ОБЩЕСТВО": "АО",
    "ОТКРЫТОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО": "ОАО",
    "БЛАГОТВОРИТЕЛЬНЫЙ ФОНД": "БФ",
    "ИНДИВИДУАЛЬНЫЙ ПРЕДПРИНИМАТЕЛЬ": "ИП",
    "ПЕРВИЧНАЯ ПРОФСОЮЗНАЯ ОРГАНИЗАЦИЯ": "ППО",
    "ФЕДЕРАЛЬНОЕ ГОСУДАРСТВЕННОЕ КАЗЕННОЕ ВОЕННОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ ВЫСШЕГО ОБРАЗОВАНИЯ": "ФГКВОУ ВО",
    "КРАЕВОЕ ГОСУДАРСТВЕННОЕ БЮДЖЕТНОЕ ПРОФЕССИОНАЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ": "КГБПОУ",
    "МУНИЦИПАЛЬНОЕ БЮДЖЕТНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ": "МБОУ",
    "МУНИЦИПАЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ ДОПОЛНИТЕЛЬНОГО ОБРАЗОВАНИЯ": "МОУ ДО",
    "МУНИЦИПАЛЬНОЕ АВТОНОМНОЕ УЧРЕЖДЕНИЕ ДОПОЛНИТЕЛЬНОГО ОБРАЗОВАНИЯ": "МАУ ДО",
    "ЧАСТНОЕ НЕКОММЕРЧЕСКОЕ ПРОФЕССИОНАЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ": "ЧНПОУ",
    "ГОСУДАРСТВЕННОЕ ОБЩЕОБРАЗОВАТЕЛЬНОЕ АВТОНОМНОЕ УЧРЕЖДЕНИЕ АМУРСКОЙ ОБЛАСТИ": "ГОАУ АО",
    "МУНИЦИПАЛЬНОЕ ДОШКОЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ КАЗЕННОЕ УЧРЕЖДЕНИЕ": "МДОКУ",
    "СРЕДНЯЯ ОБЩЕОБРАЗОВАТЕЛЬНАЯ ШКОЛА": "СОШ",
    "ГОСУДАРСТВЕННОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ СОЦИАЛЬНОГО ОБСЛУЖИВАНИЯ АМУРСКОЙ ОБЛАСТИ": "ГБУ СО АО",
    "СОЦИАЛЬНО- РЕАБИЛИТАЦИОННЫЙ ЦЕНТР ДЛЯ НЕСОВЕРШЕННОЛЕТНИХ": "СРЦН" 
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
    diagnosis_format: str = "-" 
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

    # def _get_hosp_text(self) -> str:
    #     return f"{self.hosp_date} в {self.hosp_place}" if self.hosp_date and self.hosp_place else "амбулаторное лечение"

    def _get_hosp_text(self) -> str:
    # Если оба поля не являются "-" и не пустые
        if (self.hosp_date and self.hosp_date != "-" and
            self.hosp_place and self.hosp_place != "-"):
            return f"{self.hosp_date} в {self.hosp_place}"
        return "амбулаторное лечение"

    def to_md(self) -> str:
        hosp = self._get_hosp_text()
        return f"""‼️ **{self.diagnosis_final}**
**ФИО:** {self.full_name}, {self.age}
**Дата поступления ЭИ:** {self.notification_number} от {self.notification_date}
**Место работы/учебы:** {self.organization}
**Кол-во случаев:** 1 случай
**Последнее посещение:** {self.last_visit}
**Дата заболевания:** {self.disease_date}
**Дата обращения:** {self.date_request}
**Госпитализация:** {hosp}
**Этиологическая расшифровка:** в работе
**Дополнительная информация:**
{self.additional_info}"""

    def to_plain(self) -> str:
        hosp = self._get_hosp_text()
        return f"""‼️ {self.diagnosis_final}
ФИО: {self.full_name}, {self.age}
Дата поступления ЭИ: {self.notification_number} от {self.notification_date}
Место работы/учебы: {self.organization}
Кол-во случаев: 1 случай
Последнее посещение: {self.last_visit}
Дата заболевания: {self.disease_date}
Дата обращения: {self.date_request}
Госпитализация: {hosp}
Этиологическая расшифровка: в работе
Дополнительная информация:
{self.additional_info}"""

    def to_html(self) -> str:
        hosp = self._get_hosp_text()
        # Для HTML оборачиваем в <i> и сохраняем переносы как <br>
        italic_info = self.additional_info.replace('\n', '<br>')
        return f"""‼️ <b>{self.diagnosis_final}</b><br>
<b>ФИО:</b> {self.full_name}, {self.age}<br>
<b>Дата поступления ЭИ:</b> {self.notification_number} от {self.notification_date}<br>
<b>Место работы/учебы:</b> {self.organization}<br>
<b>Кол-во случаев:</b> 1 случай<br>
<b>Последнее посещение:</b> {self.last_visit}<br>
<b>Дата заболевания:</b> {self.disease_date}<br>
<b>Дата обращения:</b> {self.date_request}<br>
<b>Госпитализация:</b> {hosp}<br>
<b>Этиологическая расшифровка:</b> в работе<br>
<b>Дополнительная информация:</b><br>
<i>{italic_info}</i>"""
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

    def __init__(self, text: str): self.text = text

    def clean_value(self, value: str) -> str:
        if not value or value == "-": return "-"
        return re.sub(r'\s+', ' ', value).strip()

    def parse(self) -> NotificationData:
        data = {}
        for key in ["full_name","age","diagnosis","diagnosis_final","notification_number",
                    "notification_date","date_request","last_visit","disease_date","hosp_date",
                    "hosp_place","additional_info"]:
            match = self.PATTERNS[key].search(self.text)
            data[key] = self.clean_value(safe_get(match))

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
            if not text: continue
            try: results.append(PDFParser(text).parse())
            except Exception as e: print(f"Ошибка: {e}")
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
        self.root.geometry("700x710")

        tk.Label(self.root, text="Перетащите PDF в окно ниже или выберите файл вручную", font=("Arial", 11)).pack(pady=10)
        
        browse_btn = tk.Label(self.root, text="Выбрать вручную", relief="raised", padx=10, pady=5, cursor="hand2")
        browse_btn.pack(pady=5)
        browse_btn.bind("<Button-1>", lambda e: self.select_files())
        browse_btn.drop_target_register(DND_FILES)
        browse_btn.dnd_bind("<<Drop>>", self.handle_drop)

        self.output_text = scrolledtext.ScrolledText(self.root, width=100, height=35, font=("impact ", 10))
        self.output_text.pack(pady=10, padx=10)
        self.output_text.drop_target_register(DND_FILES)
        self.output_text.dnd_bind("<<Drop>>", self.handle_drop)

        self.output_text.tag_config("header", foreground="black", font=("impact ", 10, "bold"))
        self.output_text.tag_config("diagnosis", foreground="red", font=("impact ", 10, "bold"))
        self.output_text.tag_config("italic", font=("Arial", 10, "italic")) 

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Копировать для MAX", 
                  command=lambda: self.copy_data(use_markdown=False), bg="#fbcff6").pack(side=tk.LEFT, padx=10)

        tk.Button(btn_frame, text="Копировать для Telegram", 
                  command=lambda: self.copy_data(use_markdown=True), bg="#e1f5fe").pack(side=tk.LEFT, padx=10)
        

    def select_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        if file_paths: self.process_files(list(file_paths))

    def handle_drop(self, event):
        file_paths = self.root.tk.splitlist(event.data)
        pdfs = [f.strip("{}") for f in file_paths if f.lower().endswith(".pdf")]
        self.process_files(pdfs)

    def process_files(self, file_paths: list[str]):
        if not file_paths: return
        self.data_blocks.clear()
        self.output_text.delete(1.0, tk.END)
        for data in PDFService.process(file_paths):
            self.data_blocks.append(data)
            self.display_clean(data)

    def display_clean(self, data: NotificationData):
        self.output_text.insert(tk.END, data.diagnosis_final + "\n", "diagnosis")
        # Список всех полей, КРОМЕ дополнительной информации
        fields = [
            ("ФИО", f"{data.full_name}, {data.age}"), 
            ("Дата поступления ЭИ", f"{data.notification_number} от {data.notification_date}"),
            ("Место работы/учебы", data.organization), 
            ("Последнее посещение", data.last_visit),
            ("Дата заболевания", data.disease_date), 
            ("Дата обращения", data.date_request),
            ("Госпитализация", data._get_hosp_text()), 
            ("Этиологическая расшифровка", "в работе"),
        ]
        
        for title, value in fields:
            self.output_text.insert(tk.END, title + ": ", "header")
            self.output_text.insert(tk.END, value + "\n")
        # Отдельно выводим Дополнительную информацию курсивом
        self.output_text.insert(tk.END, "Дополнительная информация: ", "header")
        self.output_text.insert(tk.END, data.additional_info + "\n", "italic") # Применяем тег italic
        
        self.output_text.insert(tk.END, "\n")

    def copy_data(self, use_markdown: bool):
        if not self.data_blocks:
            messagebox.showwarning("Внимание", "Нет данных для копирования")
            return

        if use_markdown:
            final_text = "\n\n---\n\n".join([d.to_md() for d in self.data_blocks])
            self.root.clipboard_clear()
            self.root.clipboard_append(final_text)
            msg = "Скопировано для мессенджера Telegram"
        else:
            plain_parts = [d.to_plain() for d in self.data_blocks]
            html_parts = [d.to_html() for d in self.data_blocks]
            final_plain = "\n\n---\n\n".join(plain_parts)
            final_html = "\n<br><br>---<br><br>\n".join(html_parts)
            
            try:
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardText(final_plain, win32clipboard.CF_UNICODETEXT)
                    html_format = win32clipboard.RegisterClipboardFormat("HTML Format")
                    html_payload = (
                        "Version:0.9\r\n"
                        "StartHTML:00000000\r\nEndHTML:00000000\r\n"
                        "StartFragment:00000000\r\nEndFragment:00000000\r\n"
                        "<html><body><!--StartFragment-->" + final_html + "<!--EndFragment--></body></html>"
                    )
                    win32clipboard.SetClipboardData(html_format, html_payload.encode("utf-8"))
                finally:
                    win32clipboard.CloseClipboard()
                msg = "Скопировано для мессенджера MAX"
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка буфера обмена: {e}")
                return

        messagebox.showinfo("Готово", msg)

# ======== Главный запуск =========
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = NotificationApp(root)
    root.mainloop()
