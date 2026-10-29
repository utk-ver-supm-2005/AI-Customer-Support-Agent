"""
Automated Test Suite for Objectives 1 and 2
Using Python's standard unittest framework.
"""

import unittest
from conversation_manager import build_conversation_context
from email_processor import process_email
from issue_analyzer import IssueAnalysis
from workflow_router import classify_and_route, SupportCategory, TicketPriority, QUEUE_MAPPING
from main import preprocess_input
from gmail_service import get_gmail_status


class TestConversationManager(unittest.TestCase):
    def test_build_conversation_context(self):
        raw = """CUSTOMER:
My app is slow.

SUPPORT:
Which page is slow?

CUSTOMER:
The billing dashboard."""
        cleaned = build_conversation_context(raw)
        self.assertIn("CUSTOMER: My app is slow.", cleaned)
        self.assertIn("SUPPORT: Which page is slow?", cleaned)
        self.assertIn("CUSTOMER: The billing dashboard.", cleaned)

    def test_single_turn_and_spacing(self):
        raw = "CUSTOMER: Hello there.   \n  "
        cleaned = build_conversation_context(raw)
        self.assertEqual(cleaned, "CUSTOMER: Hello there.")


class TestEmailProcessor(unittest.TestCase):
    def test_process_valid_email(self):
        email_text = """From: customer@example.com
Subject: Cannot download invoice

Hello support team,
I cannot download my invoice from last month.
Thank you."""
        parsed = process_email(email_text)
        self.assertEqual(parsed["sender"], "customer@example.com")
        self.assertEqual(parsed["subject"], "Cannot download invoice")
        self.assertIn("I cannot download my invoice", parsed["body"])

    def test_process_missing_headers(self):
        raw_text = "Just a raw message without standard headers."
        parsed = process_email(raw_text)
        self.assertEqual(parsed["sender"], "")
        self.assertEqual(parsed["subject"], "")
        self.assertIn("Just a raw message", parsed["body"])


class TestPreprocessInput(unittest.TestCase):
    def test_detects_thread(self):
        text = "CUSTOMER: Help!\nSUPPORT: How can I help?"
        result = preprocess_input(text)
        self.assertTrue(result.startswith("CUSTOMER: Help!"))

    def test_detects_email(self):
        text = "From: a@b.com\nSubject: Help\n\nBody here"
        result = preprocess_input(text)
        self.assertIn("Sender: a@b.com", result)
        self.assertIn("Subject: Help", result)

    def test_plain_text_passthrough(self):
        text = "Just some plain text query."
        result = preprocess_input(text)
        self.assertEqual(result, text)


class TestWorkflowRouter(unittest.TestCase):
    def test_api_technical_routing(self):
        analysis = IssueAnalysis(
            issue="API returns 401 Unauthorized",
            intent="Troubleshoot API authentication error",
            entities={"error_code": "401", "endpoint": "/v1/users", "product": "REST API"},
            context="Customer regenerated tokens but still gets 401 on /v1/users"
        )
        routed = classify_and_route(analysis)
        self.assertEqual(routed.category, SupportCategory.API_TECHNICAL)
        self.assertEqual(routed.route, QUEUE_MAPPING[SupportCategory.API_TECHNICAL])
        self.assertEqual(routed.priority, TicketPriority.HIGH)
        self.assertTrue(len(routed.routing_reason) > 0)

    def test_billing_payments_routing(self):
        analysis = IssueAnalysis(
            issue="Double charge on recent invoice",
            intent="Request refund for duplicate payment",
            entities={"invoice": "INV-1029", "amount": "$450"},
            context="Customer was billed twice on their credit card"
        )
        routed = classify_and_route(analysis)
        self.assertEqual(routed.category, SupportCategory.BILLING_PAYMENTS)
        self.assertEqual(routed.route, QUEUE_MAPPING[SupportCategory.BILLING_PAYMENTS])
        self.assertEqual(routed.priority, TicketPriority.HIGH)

    def test_account_login_routing(self):
        analysis = IssueAnalysis(
            issue="Account locked after failing 2FA code",
            intent="Unlock account and reset two factor authentication",
            entities={"username": "johndoe", "auth_method": "2FA"},
            context="User lost their phone and cannot log in"
        )
        routed = classify_and_route(analysis)
        self.assertEqual(routed.category, SupportCategory.ACCOUNT_LOGIN)
        self.assertEqual(routed.route, QUEUE_MAPPING[SupportCategory.ACCOUNT_LOGIN])
        self.assertEqual(routed.priority, TicketPriority.HIGH)

    def test_product_export_routing(self):
        analysis = IssueAnalysis(
            issue="CSV export is truncated to 50 rows",
            intent="Report bug with data export feature",
            entities={"feature": "CSV Export", "format": "CSV"},
            context="Dashboard table displays 3000 rows but download cuts off at 50"
        )
        routed = classify_and_route(analysis)
        self.assertEqual(routed.category, SupportCategory.PRODUCT_EXPORT)
        self.assertEqual(routed.route, QUEUE_MAPPING[SupportCategory.PRODUCT_EXPORT])

    def test_feature_request_routing(self):
        analysis = IssueAnalysis(
            issue="Customer wants dark mode and webhook support",
            intent="Submit product feature request and enhancement suggestion",
            entities={"feature": "Dark Mode", "integration": "Webhooks"},
            context="Customer asks if webhook alerts are on roadmap"
        )
        routed = classify_and_route(analysis)
        self.assertEqual(routed.category, SupportCategory.FEATURE_REQUEST)
        self.assertEqual(routed.route, QUEUE_MAPPING[SupportCategory.FEATURE_REQUEST])
        self.assertEqual(routed.priority, TicketPriority.LOW)

    def test_unclear_human_review_fallback_on_vague_input(self):
        analysis = IssueAnalysis(
            issue="Account is not working properly",
            intent="Request fix for broken account",
            entities={"sender": "amit@example.com"},
            context="Vague message without error code or diagnostic context"
        )
        routed = classify_and_route(analysis)
        self.assertEqual(routed.category, SupportCategory.UNCLEAR_HUMAN_REVIEW)
        self.assertEqual(routed.route, QUEUE_MAPPING[SupportCategory.UNCLEAR_HUMAN_REVIEW])
        self.assertIn("insufficient diagnostic details", routed.routing_reason.lower())


class TestInputValidation(unittest.TestCase):
    def test_empty_string_rejected(self):
        from main import process_and_route_ticket
        with self.assertRaises(ValueError):
            process_and_route_ticket("")

    def test_whitespace_string_rejected(self):
        from main import process_and_route_ticket
        with self.assertRaises(ValueError):
            process_and_route_ticket("   \n\t   ")


class TestGmailServiceGracefulFallback(unittest.TestCase):
    def test_gmail_disconnected_status(self):
        status = get_gmail_status()
        self.assertIsInstance(status, dict)
        self.assertIn("connected", status)
        self.assertFalse(status["connected"])
        self.assertIn("Fallback Mode", status["mode"])
        self.assertFalse(status["can_fetch"])


if __name__ == "__main__":
    unittest.main()
