def process_email(email_text):
    """
    Extract basic information from a raw customer-support email.

    Expected format:
    From: customer@example.com
    Subject: Some subject

    Email body...
    """

    lines = email_text.strip().splitlines()

    sender = ""
    subject = ""

    body_start = 0

    for i, line in enumerate(lines):
        if line.lower().startswith("from:"):
            sender = line[5:].strip()

        elif line.lower().startswith("subject:"):
            subject = line[8:].strip()

        elif line.strip() == "": 
            body_start = i + 1 
            break

    body = "\n".join(lines[body_start:]).strip()

    return {
        "sender": sender,
        "subject": subject,
        "body": body
    }