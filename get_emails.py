import re
import PyPDF2


def get_emails():
    with open('Annexes/trmemail.pdf', 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        lines = text.split('\n')
    
    # Regular expressions
    start_pattern = r'^[A-ZÀ-Ú ]+\s\d'  # Line starts with uppercase name followed by space and digit
    name_pattern = r'^([A-ZÀ-Ú ]+)(?=\s\d)'  # Capture name until space before digit
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'  # Regex for valid email format


    initial_emails = []
    collecting_emails = False
    for line in lines:
        if "Turma:" in line:
            collecting_emails = True
            continue
        if "Nome" in line and "RG" in line:
            data_started = True
            break
        if collecting_emails:
            emails = [email.strip() for email in line.split(',') if email.strip()]
            valid_emails = [email for email in emails if re.match(email_pattern, email)]
            initial_emails.extend(valid_emails)
        
    initial_emails_set = set(initial_emails)

    name_email_list = []
    current_entry = []
    data_started = False
    for line in lines:
        if "Nome" in line and "RG" in line:
            data_started = True
            continue
        if not data_started:
            continue
        
        # Check if the line starts a new entry
        if re.match(start_pattern, line):
            if current_entry:
                # Process the previous entry
                entry_text = ' '.join(current_entry).strip()
                name_match = re.match(name_pattern, current_entry[0])
                if name_match:
                    name = name_match.group(1).strip()
                    name = re.sub(r'\s+', ' ', name).strip()
                    emails = [email for email in initial_emails_set if email in entry_text]
                    name_email_list.append((name, emails))
            # Start a new entry
            current_entry = [line]
        elif current_entry:
            # Add line to the current entry
            current_entry.append(line)

       # Process the last entry
    if current_entry:
        entry_text = ' '.join(current_entry).strip()
        name_match = re.match(name_pattern, current_entry[0])
        if name_match:
            name = name_match.group(1).strip()
            name = re.sub(r'\s+', ' ', name).strip()
            emails = [email for email in initial_emails_set if email in entry_text]
            name_email_list.append((name, emails))
    
    return name_email_list
