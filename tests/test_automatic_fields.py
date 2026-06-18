"""Test that with no fields selected for a stream automatic fields are still replicated."""
import os
from base import ImpactBaseTest
from tap_tester.base_suite_tests.automatic_fields_test import MinimumSelectionTest


class ImpactAutomaticFieldsTest(MinimumSelectionTest, ImpactBaseTest):
    """Test that with no fields selected for a stream automatic fields are
    still replicated."""

    @staticmethod
    def name():
        return "tap_tester_impact_automatic_fields_test"

    def streams_to_test(self):
        # Exclude conversion_paths when no model_id is configured
        streams_to_exclude = set()
        if not os.getenv("TAP_IMPACT_MODEL_ID"):
            streams_to_exclude.add("conversion_paths")
        return self.expected_stream_names().difference(streams_to_exclude)
