"""
Sample Customer Support Scenarios for Demonstrating Objectives 1 and 2.
Enriched with realistic inbox metadata, ticket IDs, customer info, and knowledge links.
"""

SCENARIOS = {
    "1. API / Technical (401 Auth Error)": {
        "ticket_id": "#TECH-401",
        "title": "API 401 Unauthorized Error",
        "category": "API/Technical",
        "type": "thread",
        "sender_name": "Rahul Mehta",
        "sender_email": "rahul.mehta@devstudio.com",
        "customer_plan": "Enterprise Developer Tier",
        "customer_since": "Jan 2023",
        "avatar_initials": "RM",
        "avatar_color": "#3B82F6",
        "timestamp": "10:24 AM",
        "subject": "API access issue - 401 error",
        "snippet": "We are using version 4.2. Getting 401 Unauthorized on every request...",
        "status": "In Triage",
        "attachment": None,
        "articles": [
            "API Authentication & 401 Troubleshooting",
            "Regenerating & Scoping API Tokens",
            "API Gateway Rate Limits & Quotas"
        ],
        "content": """CUSTOMER:
My API isn't working.

SUPPORT:
Could you please tell us which API version you are using?

CUSTOMER:
We are using version 4.2. I'm getting 401 Unauthorized on every request.
I already regenerated the API token but the problem still exists."""
    },

    "2. Billing / Payments (Duplicate Invoice Charge)": {
        "ticket_id": "#BILL-1042",
        "title": "Duplicate Charge on Invoice",
        "category": "Billing/Payments",
        "type": "email",
        "sender_name": "Priya Sharma",
        "sender_email": "priya.sharma@acmecorp.com",
        "customer_plan": "Pro Subscription ($1,250/mo)",
        "customer_since": "Apr 2024",
        "avatar_initials": "PS",
        "avatar_color": "#EC4899",
        "timestamp": "Yesterday",
        "subject": "Urgent: Double billed for Invoice #INV-88921",
        "snippet": "Our card was charged twice for Invoice #INV-88921 on Oct 24th ($1,250 x 2)...",
        "status": "Awaiting Verification",
        "attachment": "bank_statement_oct2026.pdf (245 KB)",
        "articles": [
            "Handling Duplicate Subscription Charges",
            "Refund Policy & Processing SLA",
            "Invoicing & Ledger Adjustments"
        ],
        "content": """From: priya.sharma@acmecorp.com
Subject: Urgent: Double billed for Invoice #INV-88921

Hello Support Team,

Our corporate credit card was charged twice for Invoice #INV-88921 on October 24th ($1,250 x 2).
Please refund the duplicate transaction of $1,250 and issue an updated receipt immediately.

Best regards,
Priya Sharma
Finance Director"""
    },

    "3. Account / Login (Locked Out & 2FA Reset)": {
        "ticket_id": "#IAM-203",
        "title": "Account Locked Out after MFA Device Loss",
        "category": "Account/Login",
        "type": "email",
        "sender_name": "David Miller",
        "sender_email": "david.miller@enterprise.io",
        "customer_plan": "Business Tier",
        "customer_since": "Aug 2023",
        "avatar_initials": "DM",
        "avatar_color": "#8B5CF6",
        "timestamp": "2 days ago",
        "subject": "Account locked out - lost 2FA phone",
        "snippet": "Lost access to Google Authenticator. Error 'Account locked after 5 failed attempts'...",
        "status": "Identity Verification Pending",
        "attachment": None,
        "articles": [
            "Two-Factor Authentication (2FA) Reset Protocol",
            "Account Lockout Security Policies",
            "SSO Login Diagnostics"
        ],
        "content": """From: david.miller@enterprise.io
Subject: Account locked out - lost 2FA phone

Hello,

I got a new phone and lost access to my Google Authenticator 2FA device.
Now when trying to login with username david.miller, I get error 'Account locked after 5 failed authentication attempts'.
Please unlock my account and trigger an identity verification link to reset two-factor auth.

Thanks,
David Miller"""
    },

    "4. Product / Export (CSV Truncation Bug)": {
        "ticket_id": "#PROD-812",
        "title": "Analytics Dashboard CSV Export Truncated",
        "category": "Product/Export",
        "type": "thread",
        "sender_name": "Neha Verma",
        "sender_email": "neha.verma@techcorp.in",
        "customer_plan": "Growth Tier",
        "customer_since": "Nov 2024",
        "avatar_initials": "NV",
        "avatar_color": "#F97316",
        "timestamp": "2 days ago",
        "subject": "Analytics Dashboard CSV Export Truncated",
        "snippet": "Downloaded spreadsheet only has 50 rows, but our table displays 3,400 records...",
        "status": "Under Investigation",
        "attachment": "truncated_sample.csv (12 KB)",
        "articles": [
            "CSV Export Limits & Pagination Guidelines",
            "Data Export Background Worker Architecture",
            "Supported Export Formats"
        ],
        "content": """CUSTOMER:
When I click 'Export to CSV' on the monthly analytics dashboard, the downloaded spreadsheet only has 50 rows, but our table displays 3,400 records.

SUPPORT:
Does this happen in all date ranges, or specifically for October?

CUSTOMER:
It happens in all date ranges. The downloaded file cuts off after row 50 and the last line is truncated."""
    },

    "5. Feature Request (Webhooks & Dark Mode)": {
        "ticket_id": "#FEAT-505",
        "title": "Feature Request: Webhook Notifications & Dark Mode",
        "category": "Feature Request",
        "type": "email",
        "sender_name": "Alex Mercer",
        "sender_email": "alex@startup.dev",
        "customer_plan": "Developer Plan",
        "customer_since": "Feb 2024",
        "avatar_initials": "AM",
        "avatar_color": "#14B8A6",
        "timestamp": "3 days ago",
        "subject": "Feature Request: Webhook support for status alerts",
        "snippet": "Request webhook integration for Slack bot alerts, plus dark mode for developer team...",
        "status": "Backlog Review",
        "attachment": None,
        "articles": [
            "Product Roadmap Submission Process",
            "Webhook Event Specifications (Beta)",
            "Integration Request Lifecycle"
        ],
        "content": """From: alex@startup.dev
Subject: Feature Request: Webhook support for status alerts

Hi team,

We really love your product! We would love to request webhook integration so our Slack bot can receive instant alerts whenever a status changes.
Also, if your team has dark mode on the roadmap, our developer team would really appreciate it.

Keep up the great work,
Alex"""
    },

    "6. Unclear / Human Review (Vague Issue)": {
        "ticket_id": "#TRIAGE-901",
        "title": "Vague Customer Query Needing Clarification",
        "category": "Unclear/Human Review",
        "type": "email",
        "sender_name": "Amit Kumar",
        "sender_email": "amit@example.com",
        "customer_plan": "Free Starter Tier",
        "customer_since": "Oct 2026",
        "avatar_initials": "AK",
        "avatar_color": "#64748B",
        "timestamp": "3 days ago",
        "subject": "Something is not working",
        "snippet": "My account is not working properly. Please fix it as soon as possible...",
        "status": "Needs Clarification",
        "attachment": None,
        "articles": [
            "Customer Clarification Guidelines",
            "Diagnostic Information Request Templates",
            "Tier-1 Escalation Procedures"
        ],
        "content": """From: amit@example.com
Subject: Something is not working

Hello,

My account is not working properly.

Please fix it as soon as possible.

Regards,
Amit"""
    }
}
