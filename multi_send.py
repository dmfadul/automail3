import os
import re
import json
import credentials
from engine import Session
from datetime import datetime
from get_emails import get_emails
from get_course_info import get_course_info


def log(msg):
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{now} {msg}")


def clear_annexes_names():
    folder_path = "Annexes"
    for filename in os.listdir(folder_path):
        full_path = os.path.join(folder_path, filename)

        # Skip directories
        if not os.path.isfile(full_path):
            continue

        # Split name and extension
        name, ext = os.path.splitext(filename)

        # Clean the filename
        cleaned_name = re.sub(r'\s+', ' ', name.strip())

        # Construct the new filename
        new_filename = f"{cleaned_name}{ext}"
        new_full_path = os.path.join(folder_path, new_filename)

        # Only rename if the name has changed
        if filename != new_filename:
            print(f"Renaming: {filename} -> {new_filename}")
            os.rename(full_path, new_full_path)


def multi_send(subject_text, main_text):
    clear_annexes_names()
    log("Starting multi-send process...")

    course_info = get_course_info()
    if course_info is None:
        log("No course information.")
        return
    
    course_name = course_info.get("course_name")
    doc_name = course_info.get("doc_name")
    class_name = course_info.get("class_name")

    # with open("course_curr.json", "r", encoding="utf-8") as f:
    #     existing_data = json.load(f)
    
    # if existing_data and existing_data.get("class_name") == class_name:
    #     log("This course has already been processed. Restarting the sending process.")
    # else:
    
    #  Initialize the course_info.json file
    course_info["sent_emails"] = []
    with open("course_curr.json", "w", encoding="utf-8") as f:
        json.dump(course_info, f, indent=4, ensure_ascii=False)

    try:
        session = Session()
        session.login_mail(credentials.login, credentials.passwd)
    except Exception as e:
        log(f"Login failed: {e}")
        return
    
    # sent_emails = existing_data.get("sent_emails", [])
    names_emails = get_emails()
    total = len(names_emails)

    for i, (name, email_lst) in enumerate(names_emails):
        if not email_lst:
            log(f"{name} has no valid email address.")
            continue
        
        # if name in sent_emails:
        #     log(f"{name} -- email already sent -- Skipping ({i+1}/{total})")
        #     continue

        email_address = email_lst[0] # only sending to the first email address for now
        log(f"{name} -- {email_address} ({i+1}/{total})")

        try:
            session.prepare_email(
                subject=f"{subject_text}{course_name}",
                text=main_text,
                recipient=email_address
                )

            if session.attach_annex(f"{name}.pdf", doc_name):
                log(f"{name} -- Erro no anexo -- não enviado.")
                session.reset()
                continue
            
            if session.send():
                log(f"{name} -- Erro no envio -- não enviado.")
                session.reset()
                continue

            # Mark as sent only if send() was successful
            with open("course_curr.json", "r+", encoding="utf-8") as f:
                data = json.load(f)
                data["sent_emails"].append(name)
                f.seek(0)
                json.dump(data, f, indent=4, ensure_ascii=False)
                f.truncate()

        except Exception as e:
            log(f"{name} -- Erro inesperado -- não enviado. {e}")            
        
