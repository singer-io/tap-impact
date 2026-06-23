"""Test that all fields are replicated for each stream."""
import os
from base import ImpactBaseTest
from tap_tester.base_suite_tests.all_fields_test import AllFieldsTest


class ImpactAllFieldsTest(AllFieldsTest, ImpactBaseTest):
    """Ensure running the tap with all streams and fields selected results in
    the replication of all fields."""

    MISSING_FIELDS = {}

    @staticmethod
    def name():
        return "tap_tester_impact_all_fields_test"

    def streams_to_test(self):
        # Exclude conversion_paths when no model_id is configured
        streams_to_exclude = set()
        if not os.getenv("TAP_IMPACT_MODEL_ID"):
            streams_to_exclude.add("conversion_paths")
        return self.expected_stream_names().difference(streams_to_exclude)
