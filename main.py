import PyPDF2
import re
from pathlib import Path
from tkinter import Tk, Label, Text, END, filedialog, messagebox, scrolledtext
from tkinterdnd2 import TkinterDnD, DND_FILES
import os
from datetime import datetime
from tkinter import Button
from datetime import date
import datetime

output_text = None
root = TkinterDnD.Tk()

REPLACEMENTS  = {
    "МУНИЦИПАЛЬНОЕ АВТОНОМНОЕ ОБЩЕОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ": "МАОУ",
    "Государственное автономное учреждение здравоохранения Амурской области": "ГАУЗ АО",
    "Государственное автономное учреждение здравоохранения": "ГАУЗ",
    "Федеральное бюджетное учреждение здравоохранения": "ФБУЗ",
    "Государственное бюджетное учреждение здравоохранения Амурской области": "ГБУЗ АО",
    "Государственное бюджетное учреждение здравоохранения": "ГБУЗ",
    "МУНИЦИПАЛЬНОЕ АВТОНОМНОЕ ДОШКОЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ": "МАДОУ",
    "ДЕТСКИЙ САД": "ДС",
    "-      не работает": "не работает",
    "-     не  работает, пенсионер": "пенсионер",
    "Амурская областная инфекционная больница": "АОИБ",
    "Государственное бюджетное учреждение здравоохранения": "ГБУЗ",
    "Амурская областная детская клиническая больница": "АОДКБ",
    "Детская городская клиническая больница": "ДГКБ",

    "ГОРОДА БЛАГОВЕЩЕНСКА": "г.Благовещенска",
    # Добавьте другие замены по необходимости
}

def save_pdf_to_txt(text):
 # Сохранение текста в файл
    output_dir = "extracted_texts"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(output_dir, f"extracted_text_{timestamp}.txt")
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(text)

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
            #save_pdf_to_txt(text)
            
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось прочитать PDF файл: {e}")
        return None
    return text

def replace_institutions(text, REPLACEMENTS ):
    """
    Заменяет длинные названия организаций на аббревиатуры
    
    :param text: Исходный текст
    :param REPLACEMENTS : Словарь замен {long: short}
    :return: Текст с замененными названиями
    """
    for long, short in REPLACEMENTS .items():
        text = re.sub(re.escape(long), short, text, flags=re.IGNORECASE)
    return text


def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def parse_pdf_text(text):
    data = {
        'diagnosis': '',
        'diagnosis_final': '',
        'full_name': '',
        'age': '',
        'organization': '',
        'last_visit': '-',
        'disease_date': '',
        'hosp_place':'', 
        'hosp_date': '',
        'notification_number': '',
        'hospitalization': '',
        'additional_info': '',
        'phone': ''
    }

    # Извлечение диагноза
    diagnosis_match = re.search(r'Дата постановки\s*диагноза\s*(.*?)\s*Диагноз', text, re.DOTALL)
    if diagnosis_match:
        data['diagnosis'] = diagnosis_match.group(1).replace('\n', '').strip()

    # Извлечение заключительного диагноза
    diagnosis_final_match = re.search(r'Дата изменения\s*диагноза\s*(.*?)\s*Измененный/уточненный', text, re.DOTALL)
    if diagnosis_final_match:
        data['diagnosis_final'] = diagnosis_final_match.group(1).replace('\n', '').strip()
        if not data['diagnosis_final']:
            data['diagnosis_final'] = data['diagnosis']
            
    # Извлечение ФИО и возраста
   
    name_match = re.search(r'(?:Фамилия Имя Отчество|ФИО пациента)\s*[\n:]*\s*(.*?)\s*\n', text)
    age_match = re.search(r'Пол:\s*(.*?)\s* Возраст:', text)
    if name_match:
        data['full_name'] = name_match.group(1).strip()
    if age_match:
        data['age'] = age_match.group(1).strip()
        
       
       #print('Дата рождения', calculate_age(vozrast))
        
    # Социально-значимая организация
    socially_organization_match = re.search(r'Класс \(группа\)\s*(.*?)\s*Социально-значимое', text, re.DOTALL)
    #print('Социально значимая орг', socially_organization_match)
    if socially_organization_match:
        socially_organization_match = socially_organization_match.group(1).replace('\n', '').strip()
        data['social_organization'] = replace_institutions(socially_organization_match, REPLACEMENTS )

    # Место работы
    work_match = re.search(r'Адрес фактического места жительства:(.*?)Место работы/учебы/детское', text, re.DOTALL)
    if work_match:
        work_match = work_match.group(1).replace('\n', '').strip()
        data['organization'] = replace_institutions(work_match, REPLACEMENTS )
        if not data['organization']:
            data['organization'] = data['social_organization']

    # Извлечение заключительного диагноза
    diagnosis_final_match = re.search(r'Дата изменения\s*диагноза\s*(.*?)\s*Измененный/уточненный', text, re.DOTALL)
    if diagnosis_final_match:
        data['diagnosis_final'] = diagnosis_final_match.group(1).replace('\n', '').strip()
        if not data['diagnosis_final']:
            data['diagnosis_final'] = data['diagnosis']

    # Последнее посещение
    last_visit = re.search(r'учреждение\s*дд.мм.гггг\s*(.*?)\s*Дата последнего посещения места работы,', text, re.DOTALL)
    if last_visit:
        if not last_visit.group(1).strip():
            data['last_visit'] = "не указано"
        else:
            data['last_visit'] = last_visit.group(1).strip()

    # Дата заболевания
    #print(re.search(r'заполнения извещения:\s*дд.мм.гггг\s*(.*?)\s*Дата заболевания', text, re.DOTALL).group(1).strip())
    date_match = re.search(r'заполнения извещения:\s*дд.мм.гггг\s*(.*?)\s*Дата заболевания', text, re.DOTALL)
    if date_match:
        data['disease_date'] = date_match.group(1).strip()

    # Дата госпитализации
    hosp_match = re.search(r'Дата заболевания\s*дд.мм.гггг\s*(.*?)\s*Дата госпитализации', text, re.DOTALL)
    if hosp_match:
        data['hosp_date'] = hosp_match.group(1).strip()
    
    # Место госпитализации
    #print(re.search(r'Дополнительная информация/примечания, включая\s*перемещение пациента во время инкубационного периода:\s*(.*?)\s*Приписан к ЛПУ', text, re.DOTALL).group(1).strip().replace('\n', ''))
    hosp_date_match = re.search(r'Другое\s*(.*?)\s*Если да, название', text, re.DOTALL)
    if hosp_date_match:
        #hosp_date_match = hosp_date_match.replace('Государственное автономное учреждение здравоохранения Амурской области','ГАУЗ')
        hosp_date_match = hosp_date_match.group(1).replace('\n', '').strip()
        data['hosp_place'] = replace_institutions(hosp_date_match, REPLACEMENTS )

    # Номер ЭИ
    notification_number_match = re.search(r'Номер экстренного извещения\s*(Э\d+)', text, re.DOTALL)
    if notification_number_match:
        data['notification_number'] = notification_number_match.group(1)

    # Дата подачи ЭИ
    notification_date_match = re.search(r' Место работы/учебы/детское учреждение:\s*дд.мм.гггг\s*(.*?)\s*Дата заполнения формы', text, re.DOTALL)
    if notification_date_match:
        data['notification_date'] = notification_date_match.group(1).strip()
        
    # Дата обращения
    date_request_match = re.search(r' Дата госпитализации\s*дд.мм.гггг\s*(.*?)\s*Дата первичного обращения', text, re.DOTALL)
    if date_request_match:
        data['date_request'] = date_request_match.group(1).strip()

    # Дополнительная информация
    additional_info_match = re.search(r'Клиническая информация\s*(.*?)\s*Дополнительная информация/примечания, включая', text, re.DOTALL)
    if additional_info_match:
        data['additional_info'] = additional_info_match.group(1).replace('\n', '').replace('   ', ' ').replace('  ', ' ').strip()
    format_output(data)

    if data['diagnosis_final']:
            data['diagnosis'] = data['diagnosis_final']
           
    return data

def format_output(data):
    lines = [
        f"‼️ {data['diagnosis']}",
        f"ФИО: {data['full_name']}, {data['age']}",
        f"Ds: {data['diagnosis_final']}",
        f"Дата поступления ЭИ: {data['notification_number']} от {data['notification_date']}",
        f"Место работы/учебы: {data['organization']}",
        f"Последнее посещение: {data['last_visit']}",
        f"Дата заболевания: {data['disease_date']}",
        f"Дата обращения: {data['date_request']}",
        f"Госпитализация: {data['hosp_date']} в {data['hosp_place']}" if data['hosp_date'] else "Госпитализация: амбулаторное лечение",
        "Этиологическая расшифровка: в работе",
        "Дополнительная информация:",
        data['additional_info']
    ]
    return '\n'.join(lines)

def copy_text(event=None):
    root.clipboard_clear()
    # Получаем текст без форматирования
    text = output_text.get(1.0, END).replace('\n\n', '\n').strip()
    root.clipboard_append(text)

def process_file(file_path):
    text = extract_text_from_pdf(file_path)
    if text is None:
        return
    
    data = parse_pdf_text(text)
    if not data:
        messagebox.showerror("Ошибка", "Не удалось извлечь данные из PDF")
        return
    
    output = format_output(data)
    output_text.delete(1.0, END)
    output_text.insert(END, output)

def handle_drop(event):
    file_path = event.data.strip('{}')
    if file_path.lower().endswith('.pdf'):
        process_file(file_path)
    else:
        messagebox.showerror("Ошибка", "Пожалуйста, перетащите PDF файл")

def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        process_file(file_path)


def main():
    global output_text
    
    global root
    root.title("Обработка экстренных извещений для отправки в Telegram (@yudenkodanil)")
    root.geometry("900x700")

    # Элементы интерфейса
    Label(root, text="Перетащите PDF файл сюда или нажмите кнопку ниже", font=('Arial', 12)).pack(pady=10)

    browse_btn = Label(root, text="Выбрать файл", relief="raised", padx=10, pady=5, cursor="hand2")
    browse_btn.pack(pady=5)
    browse_btn.bind("<Button-1>", lambda e: browse_file())
    browse_btn.drop_target_register(DND_FILES)
    browse_btn.dnd_bind('<<Drop>>', handle_drop)

    Label(root, text="Результат:", font=('Arial', 12)).pack(pady=10)

    output_text = scrolledtext.ScrolledText(root, width=100, height=30, font=('Courier New', 10))
    output_text.pack(pady=10, padx=10)
    output_text.drop_target_register(DND_FILES)
    output_text.dnd_bind('<<Drop>>', handle_drop)

    # Кнопка копирования
    Button(root, text="Копировать результат", command=copy_text).pack(pady=5)

    # Обработчики горячих клавиш
    output_text.bind("<Control-c>", copy_text)
    output_text.bind("<Command-c>", copy_text)  # Для Mac

    root.drop_target_register(DND_FILES)
    root.dnd_bind('<<Drop>>', handle_drop)

    root.mainloop()

if __name__ == "__main__":
    main()