"""
Test Stepper Rendering and Lifecycle Stage Consistency
Ensures HTML is never emitted into code blocks and lifecycle states update properly.
"""

import unittest
from streamlit.testing.v1 import AppTest
from ticket_tracker import get_ticket, update_ticket_stage, reset_ticket, TicketStage


class TestStepperRender(unittest.TestCase):
    def test_app_stepper_no_code_blocks(self):
        at = AppTest.from_file('app.py', default_timeout=10)
        at.run()
        self.assertFalse(at.exception)
        
        # Verify that NO markdown element contains raw HTML tags in code blocks or plain text
        for m in at.markdown:
            val = m.value
            if "```" in val and "step-item" in val:
                self.fail(f"Raw step-item found inside markdown code block: {val}")
            if "<div class=\"step-item\">" in val:
                self.fail(f"Raw step-item div found inside markdown text: {val}")

    def test_lifecycle_stepper_updates(self):
        reset_ticket('#TECH-401')
        t = get_ticket('#TECH-401')
        self.assertEqual(t['stage'], 'Received')
        self.assertEqual(t['progress'], 0)
        
        update_ticket_stage('#TECH-401', TicketStage.IN_PROGRESS)
        t_ip = get_ticket('#TECH-401')
        self.assertEqual(t_ip['stage'], 'In Progress')
        self.assertEqual(t_ip['progress'], 75)
        
        update_ticket_stage('#TECH-401', TicketStage.RESOLVED)
        t_res = get_ticket('#TECH-401')
        self.assertEqual(t_res['stage'], 'Resolved')
        self.assertEqual(t_res['progress'], 100)
        
        # Reset back
        reset_ticket('#TECH-401')
        t_clean = get_ticket('#TECH-401')
        self.assertEqual(t_clean['stage'], 'Received')
        self.assertEqual(t_clean['progress'], 0)


if __name__ == '__main__':
    unittest.main()
