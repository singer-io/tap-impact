"""Mock integration tests — verify all schema fields appear in synced records.

Uses schema-driven record generation; every property in the schema JSON
should be present in at least one emitted record when all fields are selected.
"""
import unittest
from unittest.mock import MagicMock, patch

try:
    from base import ImpactBaseTest
except ImportError:
    from tests.base import ImpactBaseTest

from tap_impact.discover import discover
from tap_impact.sync import sync_endpoint

KNOWN_MISSING_FIELDS = {
}


def _make_client(response):
    c = MagicMock()
    c.base_url = "https://api.impact.com/Advertisers/mock_account_sid"
    c.get.side_effect = [response, {}]
    return c


class ImpactAllFieldsTest(ImpactBaseTest, unittest.TestCase):
    """Verify all schema fields are present when running sync with all fields selected."""

    def _get_catalog(self):
        return discover(self.config)

    def _sync_stream(self, stream_name, data_key, records,
                     bookmark_field=None, bookmark_type=None,
                     static_params=None, id_fields=None):
        """Helper: run sync_endpoint for a given stream and collect written records."""
        catalog = self._get_catalog()
        written = []
        response = {
            "@total": str(len(records)),
            "@pagesize": "100",
            data_key: records,
        }

        with patch("tap_impact.sync.singer.write_schema"), \
             patch("tap_impact.sync.singer.write_state"), \
             patch("tap_impact.sync.singer.messages.write_record",
                   side_effect=lambda s, r, time_extracted=None: written.append(r)):
            sync_endpoint(
                client=_make_client(response),
                catalog=catalog,
                state={},
                config=self.config,
                start_date="2020-01-01T00:00:00Z",
                stream_name=stream_name,
                path=data_key,
                endpoint_config={},
                static_params=static_params or {},
                bookmark_field=bookmark_field,
                bookmark_type=bookmark_type,
                data_key=data_key,
                id_fields=id_fields or ["id"],
                selected_streams=[stream_name],
            )
        return written

    def _assert_all_schema_fields_present(self, stream_name, records_written):
        """Assert every top-level field in the schema JSON is present in the records."""
        schema = self._load_schema(stream_name)
        expected_fields = set(schema.get("properties", {}).keys())
        known_missing = KNOWN_MISSING_FIELDS.get(stream_name, set())
        checkable_fields = expected_fields - known_missing

        actual_fields = set().union(*[set(r.keys()) for r in records_written]) if records_written else set()

        missing = checkable_fields - actual_fields
        self.assertEqual(
            missing, set(),
            msg=f"[{stream_name}] Fields in schema but NOT in records: {missing}. "
                f"Add to KNOWN_MISSING_FIELDS if intentionally absent.",
        )

    def test_ads_all_fields(self):
        record = self._generate_stream_record("ads")
        record["id"] = 1
        written = self._sync_stream("ads", "Ads", [record])
        self.assertGreater(len(written), 0)
        self._assert_all_schema_fields_present("ads", written)

    def test_deals_all_fields(self):
        record = self._generate_stream_record("deals")
        record["id"] = 1
        written = self._sync_stream("deals", "Deals", [record])
        self.assertGreater(len(written), 0)
        self._assert_all_schema_fields_present("deals", written)

    def test_media_partners_all_fields(self):
        record = self._generate_stream_record("media_partners")
        record["id"] = 1
        written = self._sync_stream("media_partners", "MediaPartners", [record])
        self.assertGreater(len(written), 0)
        self._assert_all_schema_fields_present("media_partners", written)

    def test_promo_codes_all_fields(self):
        record = self._generate_stream_record("promo_codes")
        record["id"] = 1
        written = self._sync_stream("promo_codes", "PromoCodes", [record])
        self.assertGreater(len(written), 0)
        self._assert_all_schema_fields_present("promo_codes", written)

    def test_invoices_all_fields(self):
        record = self._generate_stream_record("invoices")
        record["id"] = 1
        record["created_date"] = "2024-01-01T00:00:00Z"
        written = self._sync_stream(
            "invoices", "Invoices", [record],
            bookmark_field="created_date", bookmark_type="datetime",
        )
        self.assertGreater(len(written), 0)
        self._assert_all_schema_fields_present("invoices", written)

    def test_api_submissions_all_fields(self):
        record = self._generate_stream_record("api_submissions")
        record["batch_id"] = "BATCH001"
        record["submission_date"] = "2024-01-01T00:00:00Z"
        written = self._sync_stream(
            "api_submissions", "APISubmission", [record],
            bookmark_field="submission_date", bookmark_type="datetime",
            id_fields=["batch_id"],
        )
        self.assertGreater(len(written), 0)
        self._assert_all_schema_fields_present("api_submissions", written)

    def test_ftp_file_submissions_all_fields(self):
        record = self._generate_stream_record("ftp_file_submissions")
        record["batch_id"] = "FTP001"
        record["submission_date"] = "2024-01-01T00:00:00Z"
        written = self._sync_stream(
            "ftp_file_submissions", "FTPFileSubmissions", [record],
            bookmark_field="submission_date", bookmark_type="datetime",
            id_fields=["batch_id"],
        )
        self.assertGreater(len(written), 0)
        self._assert_all_schema_fields_present("ftp_file_submissions", written)
