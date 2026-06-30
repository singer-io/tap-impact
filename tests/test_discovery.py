"""Test tap discovery mode and metadata."""
import os
from base import ImpactBaseTest
from tap_tester.base_suite_tests.discovery_test import DiscoveryTest


class ImpactDiscoveryTest(DiscoveryTest, ImpactBaseTest):
    """Test tap discovery mode and metadata conforms to standards."""

    @staticmethod
    def name():
        return "tap_tester_impact_discovery_test"

    def streams_to_test(self):
        # Exclude conversion_paths when no model_id is configured
        streams_to_exclude = set()
        if not os.getenv("TAP_IMPACT_MODEL_ID"):
            streams_to_exclude.add("conversion_paths")
        return self.expected_stream_names().difference(streams_to_exclude)
