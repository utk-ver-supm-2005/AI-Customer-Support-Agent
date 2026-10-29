"""
Main Execution Script for AI Customer Support Knowledge Agent
Demonstrating Objectives 1 and 2 end-to-end.
"""

import sys
from email_processor import process_email
from conversation_manager import build_conversation_context
from issue_analyzer import analyze_customer_request
from workflow_router import classify_and_route, RoutedSupportRequest


def preprocess_input(raw_text: str) -> str:
    """
    Detect whether incoming text is a conversation thread,
    an RFC822-style email, or plain text, and normalize context.
    """
    text = raw_text.strip()
    
    # Check if it's a conversation thread
    if "CUSTOMER:" in text or "SUPPORT:" in text:
        return build_conversation_context(text)
    
    # Check if it's an email with headers
    first_lines = text.splitlines()[:5]
    has_email_header = any(
        line.lower().startswith("from:") or line.lower().startswith("subject:")
        for line in first_lines
    )
    if has_email_header:
        parsed = process_email(text)
        parts = []
        if parsed.get("sender"):
            parts.append(f"Sender: {parsed['sender']}")
        if parsed.get("subject"):
            parts.append(f"Subject: {parsed['subject']}")
        parts.append(f"Body:\n{parsed.get('body', '')}")
        return "\n".join(parts)
    
    # Fallback to direct raw text
    return text


def process_and_route_ticket(
    raw_text: str,
    source_label: str = "manual_input",
    ticket_id: str = None,
    db_path: str = None
) -> RoutedSupportRequest:
    """
    End-to-end pipeline executing Objective 1 and Objective 2.
    Tracks complaint lifecycle transitions:
      Received (0%) -> Analyzed (25%) -> Classified & Routed (50%)
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Support request input cannot be empty.")

    # Initialize / verify ticket registration if ticket_id provided
    if ticket_id:
        from ticket_tracker import get_ticket, update_ticket_stage, TicketStage
        get_ticket(ticket_id, db_path=db_path)

    # Step 1: Preprocess incoming request (Objective 1)
    cleaned_context = preprocess_input(raw_text)
    
    # Step 2: Extract issue, intent, entities, and context via Gemini (Objective 1)
    analysis = analyze_customer_request(cleaned_context)

    # Transition to Analyzed (25%) upon successful Gemini extraction
    if ticket_id:
        update_ticket_stage(
            ticket_id,
            TicketStage.ANALYZED,
            note="Objective 1: Issue & entity context extracted via Gemini",
            db_path=db_path
        )
    
    # Step 3: Classify category, assign route, priority, and reason (Objective 2)
    routed_request = classify_and_route(analysis, input_source=source_label)

    # Transition to Classified & Routed (50%) upon successful rule routing
    if ticket_id:
        update_ticket_stage(
            ticket_id,
            TicketStage.CLASSIFIED_ROUTED,
            note=f"Objective 2: Routed to {routed_request.route} ({routed_request.priority.value})",
            db_path=db_path
        )
    
    return routed_request


def print_routed_ticket(routed: RoutedSupportRequest):
    """Format and print structured support ticket output."""
    print("\n==================================================")
    print("      OBJECTIVE 1: STRUCTURED ISSUE ANALYSIS      ")
    print("==================================================")
    print(f"ISSUE   : {routed.issue}")
    print(f"INTENT  : {routed.intent}")
    print("ENTITIES:")
    if routed.entities:
        for k, v in routed.entities.items():
            print(f"  - {k}: {v}")
    else:
        print("  - (None detected)")
    print(f"CONTEXT : {routed.context}")

    print("\n==================================================")
    print("    OBJECTIVE 2: CLASSIFICATION & WORKFLOW ROUTE   ")
    print("==================================================")
    print(f"SUPPORT CATEGORY : {routed.category.value}")
    print(f"ASSIGNED QUEUE   : {routed.route}")
    print(f"PRIORITY LEVEL   : {routed.priority.value}")
    print(f"ROUTING REASON   : {routed.routing_reason}")
    print(f"SUGGESTED ACTION : {routed.suggested_action}")
    print("==================================================\n")


def main():
    import os
    from sample_scenarios import SCENARIOS

    scenario_keys = list(SCENARIOS.keys())
    raw_content = ""
    source_label = ""

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        matched_scenario = None
        if arg.isdigit() and 1 <= int(arg) <= len(scenario_keys):
            matched_scenario = scenario_keys[int(arg) - 1]
        else:
            for k in scenario_keys:
                if arg.lower() in k.lower():
                    matched_scenario = k
                    break

        if matched_scenario:
            raw_content = SCENARIOS[matched_scenario]["content"]
            source_label = f"Preset: {matched_scenario}"
        elif os.path.exists(arg):
            try:
                with open(arg, "r", encoding="utf-8") as f:
                    raw_content = f.read()
                source_label = f"File: {arg}"
            except Exception as e:
                print(f"Error reading file '{arg}': {e}")
                sys.exit(1)
        else:
            print(f"Error: Argument '{arg}' is neither an existing file nor a valid scenario number (1-6).")
            print("Usage:")
            print("  python main.py              (Runs default sample_thread.txt)")
            print("  python main.py [1-6]        (Runs one of the 6 curated scenarios)")
            print("  python main.py [file_path]  (Runs against a custom text/email file)")
            sys.exit(1)
    else:
        try:
            with open("sample_thread.txt", "r", encoding="utf-8") as f:
                raw_content = f.read()
            source_label = "sample_thread.txt (Default)"
        except Exception as e:
            print(f"Error reading sample_thread.txt: {e}")
            sys.exit(1)

    print("\n==================================================")
    print("   AI CUSTOMER SUPPORT KNOWLEDGE AGENT (CLI)     ")
    print("         DEMONSTRATING OBJECTIVES 1 & 2           ")
    print(f"Source: {source_label}")
    print("==================================================")

    print("\n[Input Content]")
    print("--------------------------------------------------")
    print(raw_content.strip())
    print("--------------------------------------------------")

    print("\n[1/2] Preprocessing input and running Gemini Issue Analysis...")
    t_id = SCENARIOS[matched_scenario].get("ticket_id") if matched_scenario else "#CLI-RUN"
    routed_result = process_and_route_ticket(raw_content, source_label=source_label, ticket_id=t_id)

    print("[2/2] Classifying and routing workflow...")
    print_routed_ticket(routed_result)

    from ticket_tracker import get_ticket
    tk_info = get_ticket(t_id)
    print(f"[Complaint Lifecycle] Status: {tk_info['stage']} ({tk_info['progress']}%)")


if __name__ == "__main__":
    main()
