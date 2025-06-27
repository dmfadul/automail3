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
    existing_annexes = set()
    folder_path = "Annexes"
    restarting = False
    for filename in os.listdir(folder_path):
        full_path = os.path.join(folder_path, filename)

        # Skip directories
        if not os.path.isfile(full_path):
            continue

        # Split name and extension
        name, ext = os.path.splitext(filename)

        # Clean the filename
        cleaned_name = re.sub(r'\s+', ' ', name.strip())

        # Skipt sent annexes
        if cleaned_name.endswith("_sent"):
            restarting = True
            continue

        # Construct the new filename
        new_filename = f"{cleaned_name}{ext}"
        new_full_path = os.path.join(folder_path, new_filename)

        if not cleaned_name == "trmemail":
            existing_annexes.add(cleaned_name)

        # Only rename if the name has changed
        if filename != new_filename:
            print(f"Renaming: {filename} -> {new_filename}")
            os.rename(full_path, new_full_path)
    
    if restarting:
        log(f"Restaring sending emails from where it stopped.")
    return existing_annexes


def multi_send(main_text):
    session = Session()
    flag = _multi_send(session, main_text)
    if flag == 0:
        log("All emails sent successfully.")
        session.end_session()


def _multi_send(session, main_text):
    existing_annexes = clear_annexes_names()
    log("Starting multi-send process...")

    course_info = get_course_info()
    if course_info is None:
        log("No course information.")
        return
    
    course_name = course_info.get("course_name")
    doc_name = course_info.get("doc_name")
    class_name = course_info.get("class_name")
    
    print("class_name:", class_name)
    
    #  Initialize the course_info.json file
    course_info["sent_emails"] = []
    with open("course_curr.json", "w", encoding="utf-8") as f:
        json.dump(course_info, f, indent=4, ensure_ascii=False)

    try:
        session.login_mail(credentials.login, credentials.passwd)
    except Exception as e:
        log(f"Login failed: {e}")
        return
    
    # sent_emails = existing_data.get("sent_emails", [])
    names_emails = get_emails()
    total = len(names_emails)
    sent = 0

    for i, (name, email_lst) in enumerate(names_emails):
        # Check if the name is in the email list
        if not email_lst:
            log(f"{name} has no valid email address -- Skipping ({i+1}/{total}/{sent})")
            continue

        # Check if the name is on the existing annexes list
        if name not in existing_annexes:
            log(f"{name} -- No annex found -- Skipping ({i+1}/{total}/{sent})")
            continue
        
        email_address = email_lst[0] # only sending to the first email address for now
        sent += 1
        log(f"{name} -- {email_address} ({i+1}/{total}/{sent})")

        if doc_name == "Certificado":
            subject_text = "Certidão de Conclusão de Curso - "
        elif doc_name == "Historico":
            subject_text = "Histórico Escolar do Curso - "
        else:
            log(f"{name} -- Unknown document type -- not sent.")
            sent -= 1
            continue

        try:
            session.prepare_email(
                subject=f"{subject_text}{course_name}",
                text=main_text,
                recipient=email_address
                )

            if session.attach_annex(f"{name}.pdf", doc_name):
                log(f"{name} -- Erro no anexo -- não enviado.")
                sent -= 1
                session.reset()
                continue
            
            if session.send():
                log(f"{name} -- Erro no envio -- não enviado.")
                sent -= 1
                session.reset()
                continue

            # Mark as sent only if send() was successful
            with open("course_curr.json", "r+", encoding="utf-8") as f:
                data = json.load(f)
                data["sent_emails"].append(name)
                f.seek(0)
                json.dump(data, f, indent=4, ensure_ascii=False)
                f.truncate()

            script_dir = os.path.dirname(os.path.abspath(__file__))
            os.rename(
                os.path.join(script_dir, "Annexes", f"{name}.pdf"),
                os.path.join("Annexes", f"{name}_sent.pdf")
            )
        except Exception as e:
            log(f"{name} -- Erro inesperado -- não enviado. {e}")            
            sent -= 1
            
    return 0
