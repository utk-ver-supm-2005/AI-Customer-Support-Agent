"""
Workflow Router Module (Objective 2)

Classifies customer-support requests into meaningful support categories
and establishes an initial workflow route and priority for each identified intent.
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from issue_analyzer import IssueAnalysis


class SupportCategory(str, Enum):
    BILLING_PAYMENTS = "Billing/Payments"
    ACCOUNT_LOGIN = "Account/Login"
    API_TECHNICAL = "API/Technical"
    PRODUCT_EXPORT = "Product/Export"
    FEATURE_REQUEST = "Feature Request"
    UNCLEAR_HUMAN_REVIEW = "Unclear/Human Review"


class TicketPriority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RoutedSupportRequest(BaseModel):
    """
    Structured result combining Objective 1 extraction with
    Objective 2 category classification, workflow route, and routing reason.
    """
    # Objective 1 extracted fields
    issue: str = Field(description="A concise description of the customer's main problem.")
    intent: str = Field(description="The main reason or purpose of the customer's support request.")
    entities: Dict[str, str] = Field(default_factory=dict, description="Extracted entities.")
    context: str = Field(description="Important conversational or historical information.")

    # Objective 2 routing fields
    category: SupportCategory = Field(description="Support category.")
    route: str = Field(description="Target workflow team or queue.")
    routing_reason: str = Field(description="Explicit explanation of why this route was selected.")
    priority: TicketPriority = Field(description="Operational priority level.")
    suggested_action: str = Field(description="Immediate recommended next action for support agents.")
    input_source: str = Field(default="manual_input", description="Origin of request (sample, manual, gmail).")


# Route target mapping
QUEUE_MAPPING = {
    SupportCategory.BILLING_PAYMENTS: "Finance & Billing Operations",
    SupportCategory.ACCOUNT_LOGIN: "Identity & Access Management (IAM)",
    SupportCategory.API_TECHNICAL: "Developer Support & Tier-2 Engineering",
    SupportCategory.PRODUCT_EXPORT: "Product Operations Desk",
    SupportCategory.FEATURE_REQUEST: "Product Management Backlog",
    SupportCategory.UNCLEAR_HUMAN_REVIEW: "Tier-1 Triage & Manual Clarification"
}

# Generic/vague phrases indicating human clarification is needed
VAGUE_PATTERNS = [
    "not working properly",
    "something is not working",
    "it's broken",
    "its broken",
    "please fix it",
    "please help",
    "help me",
    "not working",
    "need assistance",
    "having trouble"
]


def _is_vague_or_insufficient(analysis: IssueAnalysis) -> bool:
    """
    Check if the extracted issue/intent is too vague or lacks meaningful context/entities.
    """
    combined_text = f"{analysis.issue} {analysis.intent}".lower()
    
    # If meaningful technical entities exist (error code, invoice #, endpoint), it's likely not vague
    informative_entity_keys = {"error_code", "status_code", "invoice", "invoice_number", "transaction_id", "endpoint", "version"}
    has_informative_entity = any(k.lower() in informative_entity_keys for k in analysis.entities.keys())
    if has_informative_entity:
        return False

    # Check if text is dominated by vague phrases without specifics
    for vague in VAGUE_PATTERNS:
        if vague in combined_text and len(analysis.entities) <= 1:
            # Check if entities only has something generic like account without specific error
            return True

    words = combined_text.split()
    if len(words) < 5 and len(analysis.entities) == 0:
        return True

    return False


def classify_and_route(analysis: IssueAnalysis, input_source: str = "manual_input") -> RoutedSupportRequest:
    """
    Deterministically classify an IssueAnalysis and assign a workflow route,
    priority, and explicit routing reason.
    """
    issue_lower = analysis.issue.lower()
    intent_lower = analysis.intent.lower()
    context_lower = analysis.context.lower()
    entities_lower = {k.lower(): str(v).lower() for k, v in analysis.entities.items()}

    # Combined corpus for keyword scoring
    corpus = f"{issue_lower} {intent_lower} {context_lower} {' '.join(entities_lower.values())} {' '.join(entities_lower.keys())}"

    # First check: Insufficient/vague input fallback
    if _is_vague_or_insufficient(analysis):
        return RoutedSupportRequest(
            issue=analysis.issue,
            intent=analysis.intent,
            entities=analysis.entities,
            context=analysis.context,
            category=SupportCategory.UNCLEAR_HUMAN_REVIEW,
            route=QUEUE_MAPPING[SupportCategory.UNCLEAR_HUMAN_REVIEW],
            routing_reason="Request contains insufficient diagnostic details or vague problem description. Fallback to manual human clarification.",
            priority=TicketPriority.MEDIUM,
            suggested_action="Contact customer for reproduction steps, error logs, or affected account details.",
            input_source=input_source
        )

    # 1. API / Technical
    api_signals = ["api", "endpoint", "401", "403", "500", "502", "503", "unauthorized", "token", "bearer", "curl", "sdk", "rate limit", "payload", "timeout", "http"]
    matched_api = [s for s in api_signals if s in corpus]
    has_api_entity = any(k in ["error_code", "status_code", "endpoint", "api_version"] or "api" in str(v) for k, v in entities_lower.items())
    
    if len(matched_api) >= 1 or has_api_entity:
        error_code = analysis.entities.get("error_code") or analysis.entities.get("status_code")
        reason = f"Matched API/Technical markers ({', '.join(matched_api[:3])})"
        if error_code:
            reason += f" with error code '{error_code}'"
        
        is_high = any(code in corpus for code in ["401", "403", "500", "502", "503", "unauthorized", "timeout", "rate limit"])
        priority = TicketPriority.HIGH if is_high else TicketPriority.MEDIUM

        return RoutedSupportRequest(
            issue=analysis.issue,
            intent=analysis.intent,
            entities=analysis.entities,
            context=analysis.context,
            category=SupportCategory.API_TECHNICAL,
            route=QUEUE_MAPPING[SupportCategory.API_TECHNICAL],
            routing_reason=reason + ".",
            priority=priority,
            suggested_action="Inspect API gateway telemetry, check token scopes, and investigate endpoint service logs.",
            input_source=input_source
        )

    # 2. Billing / Payments
    billing_signals = ["billing", "payment", "charge", "invoice", "refund", "subscription", "credit card", "overcharged", "double charge", "pricing", "receipt", "transaction", "bank"]
    matched_billing = [s for s in billing_signals if s in corpus]
    has_billing_entity = any(k in ["invoice", "invoice_number", "transaction_id", "amount", "charge"] for k in entities_lower.keys())

    if len(matched_billing) >= 1 or has_billing_entity:
        reason = f"Matched Billing & Payment markers ({', '.join(matched_billing[:3])})"
        is_high = any(w in corpus for w in ["double charge", "overcharged", "refund", "unauthorized charge", "failed payment"])
        priority = TicketPriority.HIGH if is_high else TicketPriority.MEDIUM

        return RoutedSupportRequest(
            issue=analysis.issue,
            intent=analysis.intent,
            entities=analysis.entities,
            context=analysis.context,
            category=SupportCategory.BILLING_PAYMENTS,
            route=QUEUE_MAPPING[SupportCategory.BILLING_PAYMENTS],
            routing_reason=reason + ".",
            priority=priority,
            suggested_action="Review payment gateway transaction logs, inspect invoice records, and process refund or ledger adjustment.",
            input_source=input_source
        )

    # 3. Account / Login
    account_signals = ["login", "log in", "sign in", "signin", "password", "reset password", "account locked", "locked out", "2fa", "mfa", "otp", "two-factor", "sso", "credentials"]
    matched_account = [s for s in account_signals if s in corpus]
    has_account_entity = any(k in ["username", "user_id", "account_id"] for k in entities_lower.keys())

    if len(matched_account) >= 1 or has_account_entity:
        reason = f"Matched Account & Authentication access markers ({', '.join(matched_account[:3])})"
        is_high = any(w in corpus for w in ["locked", "locked out", "cannot login", "unable to login", "reset password"])
        priority = TicketPriority.HIGH if is_high else TicketPriority.MEDIUM

        return RoutedSupportRequest(
            issue=analysis.issue,
            intent=analysis.intent,
            entities=analysis.entities,
            context=analysis.context,
            category=SupportCategory.ACCOUNT_LOGIN,
            route=QUEUE_MAPPING[SupportCategory.ACCOUNT_LOGIN],
            routing_reason=reason + ".",
            priority=priority,
            suggested_action="Verify user identity, inspect failed authentication logs, and assist with password or MFA unlock.",
            input_source=input_source
        )

    # 4. Product / Export
    export_signals = ["export", "download", "csv", "pdf", "excel", "report", "spreadsheet", "truncated", "missing rows", "exporting"]
    matched_export = [s for s in export_signals if s in corpus]

    if len(matched_export) >= 1:
        reason = f"Matched Product Export & Reporting markers ({', '.join(matched_export[:3])})"
        return RoutedSupportRequest(
            issue=analysis.issue,
            intent=analysis.intent,
            entities=analysis.entities,
            context=analysis.context,
            category=SupportCategory.PRODUCT_EXPORT,
            route=QUEUE_MAPPING[SupportCategory.PRODUCT_EXPORT],
            routing_reason=reason + ".",
            priority=TicketPriority.MEDIUM,
            suggested_action="Audit export worker background jobs, verify row export bounds, and supply manually generated export if needed.",
            input_source=input_source
        )

    # 5. Feature Request
    feature_signals = ["feature request", "feature", "would love", "suggestion", "enhancement", "roadmap", "add option", "dark mode", "integrate with", "requesting a new"]
    matched_feature = [s for s in feature_signals if s in corpus]

    if len(matched_feature) >= 1:
        reason = f"Matched Feature Request & Enhancement indicators ({', '.join(matched_feature[:3])})"
        return RoutedSupportRequest(
            issue=analysis.issue,
            intent=analysis.intent,
            entities=analysis.entities,
            context=analysis.context,
            category=SupportCategory.FEATURE_REQUEST,
            route=QUEUE_MAPPING[SupportCategory.FEATURE_REQUEST],
            routing_reason=reason + ".",
            priority=TicketPriority.LOW,
            suggested_action="Log feature feedback into product management roadmap backlog and tag relevant user persona.",
            input_source=input_source
        )

    # Fallback: Unclear / Human Review
    return RoutedSupportRequest(
        issue=analysis.issue,
        intent=analysis.intent,
        entities=analysis.entities,
        context=analysis.context,
        category=SupportCategory.UNCLEAR_HUMAN_REVIEW,
        route=QUEUE_MAPPING[SupportCategory.UNCLEAR_HUMAN_REVIEW],
        routing_reason="Request did not match standard automated classification signatures. Routed for human triage.",
        priority=TicketPriority.MEDIUM,
        suggested_action="Assign to tier-1 agent for initial assessment and customer follow-up.",
        input_source=input_source
    )

