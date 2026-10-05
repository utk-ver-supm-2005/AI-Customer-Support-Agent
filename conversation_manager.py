def build_conversation_context(thread_text):
    """
    Convert a customer-support conversation thread into
    a clean text representation for the AI analyzer.
    """

    lines = thread_text.strip().splitlines()

    conversation = []
    current_sender = None
    current_message = []

    for line in lines:

        # Detect the beginning of a new message
        if line.startswith("CUSTOMER:"):
            if current_sender is not None:
                conversation.append(
                    f"{current_sender}: {' '.join(current_message).strip()}"
                )

            current_sender = "CUSTOMER"
            current_message = []

        elif line.startswith("SUPPORT:"):
            if current_sender is not None:
                conversation.append(
                    f"{current_sender}: {' '.join(current_message).strip()}"
                )

            current_sender = "SUPPORT"
            current_message = []

        elif line.strip():
            current_message.append(line.strip())

    # Add the final message
    if current_sender is not None:
        conversation.append(
            f"{current_sender}: {' '.join(current_message).strip()}"
        )

    return "\n".join(conversation)