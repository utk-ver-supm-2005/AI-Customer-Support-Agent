from email_processor import process_email
from issue_analyzer import analyze_customer_request
from conversation_manager import build_conversation_context


def main():

    # Read customer-support conversation thread
    with open("sample_thread.txt", "r", encoding="utf-8") as file:
        raw_thread = file.read()

    print("\n========================================")
    print(" AI CUSTOMER SUPPORT KNOWLEDGE AGENT")
    print("         OBJECTIVE 1")
    print("========================================\n")

    print("CONVERSATION THREAD")
    print("----------------------------")
    print(raw_thread)

    # Build clean conversation context
    conversation_context = build_conversation_context(raw_thread)

    print("\nCLEANED CONVERSATION CONTEXT")
    print("----------------------------")
    print(conversation_context)

    print("\nAnalyzing conversation...\n")

    # Analyze complete conversation using Gemini
    analysis = analyze_customer_request(conversation_context)

    print("========================================")
    print("STRUCTURED ISSUE ANALYSIS")
    print("========================================")

    print("\nISSUE")
    print(analysis.issue)

    print("\nINTENT")
    print(analysis.intent)

    print("\nENTITIES")
    for key, value in analysis.entities.items():
        print(f"{key}: {value}")

    print("\nCONTEXT")
    print(analysis.context)

    print("\n========================================")
    print("Objective 1 thread analysis completed.")
    print("========================================\n")


if __name__ == "__main__":
    main()