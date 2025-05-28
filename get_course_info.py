import os
import re
import json
import PyPDF2
from unidecode import unidecode


def get_class_name():
    with open('Annexes/trmemail.pdf', 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = reader.pages[0].extract_text()

    class_pattern = r'Turma:\s*(.+)'
    match = re.search(class_pattern, text)
    if not match:    
        print("Turma não encontrada no documento.")
        return None
    
    class_name = match.group(1).strip()
    class_name = re.sub(r'\s+', ' ', class_name).strip()
    return class_name


def confirm_course_name(current_name):
    with open("courses.json", "r") as file:
        existing_names = json.load(file)

    if not current_name in existing_names:
        print(f"O CURSO {current_name} NÃO ESTÁ CADASTRADO.\nCADASTRAR CURSO {current_name}? S/n", end=" ")
        response = input(" ").strip().lower()
        if response == "s" or response == "":
            existing_names.append(current_name)
            with open("course_names.json", "w") as file:
                json.dump(existing_names, file, indent=4)
        else:
            print("Curso não cadastrado. Cancelando envio.")
            return False
    
    return True


def get_course_info():
    folder_path = "Annexes"
    files = os.listdir(folder_path)

    for file in files:
        if file is None or file == "trmemail.pdf":
            continue
        
        file_path = os.path.join(folder_path, file)
        with open(file_path, 'rb') as file:
            try:
                reader = PyPDF2.PdfReader(file)
            except PyPDF2.errors.PdfReadError:
                continue

            text = ""
            for page in reader.pages:
                text += unidecode(page.extract_text())

        is_history = ("Historico" in text) and ("Escolar" in text)


        print(is_history)
        if is_history:
            doc_name = "Historico"
            match = re.search(r'CURSO DE\s+(.+?)(?:\s+C\.Hor\.:|\n)', text, re.IGNORECASE)   
        else:
            doc_name = "Certificado"
            course_pattern = r'"(.*?)"'
            match = re.search(course_pattern, text)
        
        if not match:
            return None      
        
        course_name = match.group(1)
        course_name = re.sub(r'\s+', ' ', course_name).strip()
        
        if not confirm_course_name(course_name):
            return None

        class_name = get_class_name()
        if class_name is None:
            return None
        
        return {"course_name": course_name,
                "doc_name": doc_name,
                "class_name": class_name,}
