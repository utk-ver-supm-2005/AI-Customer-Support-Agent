"""
Unit Tests for Ticket Lifecycle Progress Tracking (ticket_tracker.py)
Validates independent progress tracking, persistence, state transitions,
failure handling, and SQLite recovery.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from ticket_tracker import (
    TicketStage,
    STAGE_PROGRESS,
    get_stage_progress,
    init_db,
    get_ticket,
    update_ticket_stage,
    get_all_tickets,
    reset_ticket,
    reset_all_tickets,
)
from main import process_and_route_ticket


class TestTicketLifecycleTracker(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file for isolated testing
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.temp_db_fd)
        init_db(self.temp_db_path)

    def tearDown(self):
        # Clean up temporary database file
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    def test_lifecycle_stage_percentages(self):
        """Verify each lifecycle stage maps to exact predefined percentage."""
        self.assertEqual(get_stage_progress(TicketStage.RECEIVED), 0)
        self.assertEqual(get_stage_progress(TicketStage.ANALYZED), 25)
        self.assertEqual(get_stage_progress(TicketStage.CLASSIFIED_ROUTED), 50)
        self.assertEqual(get_stage_progress(TicketStage.IN_PROGRESS), 75)
        self.assertEqual(get_stage_progress(TicketStage.RESOLVED), 100)

        # String normalization tests
        self.assertEqual(get_stage_progress("Received"), 0)
        self.assertEqual(get_stage_progress("Analyzed"), 25)
        self.assertEqual(get_stage_progress("Classified & Routed"), 50)
        self.assertEqual(get_stage_progress("In Progress"), 75)
        self.assertEqual(get_stage_progress("Resolved"), 100)

    def test_initial_state_is_received_0_percent(self):
        """Verify all demo tickets and new tickets start at Received (0%)."""
        ticket = get_ticket("#TECH-401", db_path=self.temp_db_path)
        self.assertEqual(ticket["stage"], TicketStage.RECEIVED.value)
        self.assertEqual(ticket["progress"], 0)

        custom = get_ticket("#CUSTOM-NEW-01", db_path=self.temp_db_path)
        self.assertEqual(custom["stage"], TicketStage.RECEIVED.value)
        self.assertEqual(custom["progress"], 0)

    def test_independent_ticket_states(self):
        """Verify that updating one ticket does not affect other tickets."""
        t1 = update_ticket_stage("#TECH-401", TicketStage.IN_PROGRESS, "Engineer working", db_path=self.temp_db_path)
        self.assertEqual(t1["stage"], TicketStage.IN_PROGRESS.value)
        self.assertEqual(t1["progress"], 75)

        # Other tickets must still be at Received (0%)
        t2 = get_ticket("#BILL-1042", db_path=self.temp_db_path)
        self.assertEqual(t2["stage"], TicketStage.RECEIVED.value)
        self.assertEqual(t2["progress"], 0)

        t3 = get_ticket("#IAM-203", db_path=self.temp_db_path)
        self.assertEqual(t3["stage"], TicketStage.RECEIVED.value)
        self.assertEqual(t3["progress"], 0)

        # Update t2 to Resolved
        t2_updated = update_ticket_stage("#BILL-1042", TicketStage.RESOLVED, "Refund verified", db_path=self.temp_db_path)
        self.assertEqual(t2_updated["stage"], TicketStage.RESOLVED.value)
        self.assertEqual(t2_updated["progress"], 100)

        # Verify t1 remains In Progress (75%)
        t1_check = get_ticket("#TECH-401", db_path=self.temp_db_path)
        self.assertEqual(t1_check["stage"], TicketStage.IN_PROGRESS.value)
        self.assertEqual(t1_check["progress"], 75)

    def test_persistence_across_reconnect_and_restart(self):
        """Simulate application restart by reading directly from a new SQLite connection."""
        update_ticket_stage("#PROD-812", TicketStage.CLASSIFIED_ROUTED, "Routed to Engineering", db_path=self.temp_db_path)

        # Simulate complete app restart: new connection reading from disk
        restarted_ticket = get_ticket("#PROD-812", db_path=self.temp_db_path)
        self.assertEqual(restarted_ticket["stage"], TicketStage.CLASSIFIED_ROUTED.value)
        self.assertEqual(restarted_ticket["progress"], 50)
        self.assertTrue(len(restarted_ticket["history"]) >= 2)

    def test_manual_status_controls_in_progress_and_resolved(self):
        """Test authorized demo user transitions: In Progress (75%) and Resolved (100%)."""
        t = update_ticket_stage("#FEAT-505", TicketStage.IN_PROGRESS, "Sprint triage", db_path=self.temp_db_path)
        self.assertEqual(t["stage"], "In Progress")
        self.assertEqual(t["progress"], 75)

        t = update_ticket_stage("#FEAT-505", TicketStage.RESOLVED, "Logged into backlog", db_path=self.temp_db_path)
        self.assertEqual(t["stage"], "Resolved")
        self.assertEqual(t["progress"], 100)

        # Test reset
        t = reset_ticket("#FEAT-505", db_path=self.temp_db_path)
        self.assertEqual(t["stage"], "Received")
        self.assertEqual(t["progress"], 0)

    def test_failed_analysis_prevents_progress_advancement(self):
        """Verify that analysis failure leaves ticket at Received (0%) without advancement."""
        ticket_id = "#FAIL-TEST-01"
        get_ticket(ticket_id, db_path=self.temp_db_path)

        # Empty text must raise ValueError and NOT advance ticket
        with self.assertRaises(ValueError):
            process_and_route_ticket("", ticket_id=ticket_id)

        status_after_fail = get_ticket(ticket_id, db_path=self.temp_db_path)
        self.assertEqual(status_after_fail["stage"], TicketStage.RECEIVED.value)
        self.assertEqual(status_after_fail["progress"], 0)

        # Simulated exception in analyze_customer_request
        with patch("main.analyze_customer_request", side_effect=RuntimeError("Gemini API error")):
            with self.assertRaises(RuntimeError):
                process_and_route_ticket("Valid message text that fails during AI extraction", ticket_id=ticket_id)

        # Ticket must still be at Received (0%)
        status_after_ai_fail = get_ticket(ticket_id, db_path=self.temp_db_path)
        self.assertEqual(status_after_ai_fail["stage"], TicketStage.RECEIVED.value)
        self.assertEqual(status_after_ai_fail["progress"], 0)

    @patch("main.analyze_customer_request")
    def test_pipeline_advances_to_analyzed_and_classified_routed(self, mock_analyze):
        """Verify process_and_route_ticket advances ticket to Analyzed (25%) then Classified & Routed (50%)."""
        from issue_analyzer import IssueAnalysis
        mock_analyze.return_value = IssueAnalysis(
            issue="API 401 Unauthorized Error",
            intent="Resolve API key authentication failure",
            entities={"code": "401", "endpoint": "/v1/data"},
            context="User receiving 401 error on API calls"
        )
        ticket_id = "#AUTO-TEST-01"
        res = process_and_route_ticket(
            "We are getting 401 unauthorized errors",
            source_label="Test Pipeline",
            ticket_id=ticket_id,
            db_path=self.temp_db_path
        )
        
        ticket = get_ticket(ticket_id, db_path=self.temp_db_path)
        self.assertEqual(ticket["stage"], TicketStage.CLASSIFIED_ROUTED.value)
        self.assertEqual(ticket["progress"], 50)
        # Check history has Received -> Analyzed -> Classified & Routed
        stages = [h["stage"] for h in ticket["history"]]
        self.assertIn("Received", stages)
        self.assertIn("Analyzed", stages)
        self.assertIn("Classified & Routed", stages)


if __name__ == "__main__":
    unittest.main()
