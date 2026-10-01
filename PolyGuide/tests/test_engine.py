import unittest
from copy import deepcopy
from engine import ChatEngine

class TestEngine(unittest.TestCase):
    def setUp(self):
        self.bot = ChatEngine()

    def test_admission_follow_up(self):
        self.bot.respond("How to take admission?")
        self.assertEqual(self.bot.state.screen, "admission_qualification")
        r = self.bot.respond("10th pass")
        self.assertEqual(self.bot.state.qualification, "10th")
        self.assertIn("Eligibility", r.text)
        self.assertIn("Documents", r.choices)
        self.assertIn("not been verified", self.bot.respond("Documents").text)

    def test_fee_follow_up(self):
        self.bot.respond("Fees")
        self.assertEqual(self.bot.state.screen, "fees_entry")
        self.bot.respond("Direct second year")
        self.assertEqual(self.bot.state.screen, "fees_department")
        r = self.bot.respond("Computer Engineering")
        self.assertEqual(self.bot.state.screen, "fees_result")
        self.assertIn("Direct second year fees", r.text)
        self.assertNotIn("12345", r.text)

    def test_combined_fee_question(self):
        self.bot.respond("yearly fees for computer engineering direct second year admission")
        self.assertEqual(self.bot.state.screen, "fees_result")
        self.assertEqual(self.bot.state.entry, "direct_second_year")

    def test_fee_typo(self):
        self.bot.respond("What are the feees?")
        self.assertEqual(self.bot.state.screen, "fees_entry")

    def test_admission_typo(self):
        self.bot.respond("admision")
        self.assertEqual(self.bot.state.screen, "admission_qualification")

    def test_department_typo(self):
        self.bot.respond("mecanical")
        self.assertEqual(self.bot.state.department, "mechanical")

    def test_exact_token_matching(self):
        self.assertIsNone(self.bot.intent(self.bot.normalize("coffee")))
        self.assertIn("couldn't match", self.bot.respond("coffee").text)

    def test_back_restores_prompt(self):
        self.bot.respond("Fees")
        self.bot.respond("First year")
        self.bot.respond("Civil")
        self.bot.respond("Back")
        self.assertEqual(self.bot.state.screen, "fees_department")
        self.bot.respond("Back")
        self.assertEqual(self.bot.state.screen, "fees_entry")

    def test_home_reset(self):
        self.bot.respond("admission")
        self.bot.respond("12th pass")
        self.bot.respond("Home")
        self.assertEqual(self.bot.state.qualification, "")
        self.assertEqual(len(self.bot.navigation_stack), 0)

    def test_topic_switch(self):
        self.bot.respond("Admission")
        self.bot.respond("Contact")
        self.assertEqual(self.bot.state.screen, "contact")

    def test_no_route_guess(self):
        self.bot.respond("Fees")
        self.bot.respond("12th pass")
        self.assertEqual(self.bot.state.screen, "fees_entry")
        self.assertEqual(self.bot.state.entry, "")

    def test_unverified_data_blocked(self):
        rec = {"text":"DO NOT DISPLAY", "source":"test", "updated":"test", "verified":False}
        self.assertNotIn("DO NOT DISPLAY", self.bot.fact(rec, "Fees"))

    def test_missing_source_blocked(self):
        rec = {"text":"DO NOT DISPLAY", "verified":True, "updated":"test"}
        self.assertNotIn("DO NOT DISPLAY", self.bot.fact(rec, "Fees"))

    def test_verified_record_rendered(self):
        rec = {"text":"TEST FIXTURE ONLY", "source":"Unit-test fixture", "updated":"Test date", "verified":True}
        self.assertIn("TEST FIXTURE ONLY", self.bot.fact(rec, "Fees"))
        self.assertIn("Source:", self.bot.fact(rec, "Fees"))

    def test_custom_department_menu(self):
        data = deepcopy(self.bot.data)
        data["departments"]["electrical"] = {"name":"Electrical Engineering", "aliases":["electrical"], "overview":{}}
        bot = ChatEngine(data)
        self.assertIn("Electrical Engineering", bot.respond("Courses").choices)
        self.assertIn("not been verified", bot.respond("Electrical Engineering").text)

    def test_history_bounded(self):
        for i in range(205):
            self.bot.respond("hello")
        self.assertEqual(len(self.bot.history), 200)

    def test_empty_input(self):
        self.assertIn("Type a question", self.bot.respond("").text)

    def test_long_input(self):
        self.assertIn("1,000", self.bot.respond("a" * 1001).text)

    def test_tree(self):
        self.assertEqual(self.bot.tree_choices("Home"), ["Admission", "Courses", "Fees", "More"])
        self.assertIn("Contact", self.bot.tree_choices("More"))

    def test_invalid_data(self):
        with self.assertRaises(ValueError):
            ChatEngine({})

if __name__ == "__main__":
    unittest.main()
