from __future__ import annotations

import os
import unittest

import legacy_ui_server


class LegacyUiServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.original_cwd = os.getcwd()
        os.chdir(legacy_ui_server.LEGACY_SCRIPTS)
        cls.client = legacy_ui_server.create_app().test_client()

    @classmethod
    def tearDownClass(cls) -> None:
        os.chdir(cls.original_cwd)

    def test_translation_helper_is_ground_truth_fixture_without_external_io(self) -> None:
        response = self.client.get("/js/business/helpers/translate.js")
        self.addCleanup(response.close)
        self.assertEqual(response.status_code, 200)
        javascript = response.get_data(as_text=True)
        self.assertIn("CITYWALK_TRANSLATION_FIXTURE_SHORT", javascript)
        self.assertIn("CITYWALK_TRANSLATION_FIXTURE_LONG", javascript)
        self.assertIn("27km-long Large Hadron Collider", javascript)
        self.assertNotIn("api-free.deepl.com", javascript)
        self.assertNotIn("auth_key", javascript)
        self.assertNotIn("fetch(", javascript)
        self.assertEqual(javascript.count("detected_source_language"), 1)

    def test_selected_content_gets_editable_clone_in_test_runtime(self) -> None:
        response = self.client.get(
            "/js/business/view_controllers/createguide_view_controller.js"
        )
        self.addCleanup(response.close)
        self.assertEqual(response.status_code, 200)
        javascript = response.get_data(as_text=True)
        restoration = (
            "_this2.editContentView.editingContent = "
            "EditingContent.fromContent(content);"
        )
        self.assertEqual(javascript.count(restoration), 1)


if __name__ == "__main__":
    unittest.main()
