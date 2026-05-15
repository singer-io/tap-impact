"""Mock integration tests — automatic (primary key + replication key) fields only.

Verifies that even when no optional fields are selected, automatic fields
(primary keys and replication keys) are always present in synced records.
"""
import unittest
from unittest.mock import MagicMock, patch

try:
    from base import ImpactBaseTest
except ImportError:
    from tests.base import ImpactBaseTest

from tap_impact.discover import discover
from tap_impact.sync import sync_endpoint


def _make_client(response):
    c = MagicMock()
    c.base_url = "https://api.impact.com/Advertisers/mock_account_sid"
    c.get.side_effect = [response, {}]
    return c


class ImpactAutomaticFieldsTest(ImpactBaseTest, unittest.TestCase):
    """Verify automatic fields are always replicated, even with minimal selection."""

    def _get_catalog(self):
        return discover(self.config)

    def _sync_stream_minimal(self, stream_name, data_key, records,
                             bookmark_field=None, bookmark_type=None,
                             static_params=None, id_fields=None):
        """Run sync for a stream and return all written records."""
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

    def _assert_automatic_fields_present(self, stream_name, records_written):
        """Assert that PKs and replication keys are present in each record."""
        meta = self.expected_metadata()[stream_name]
        required_fields = set(meta[self.PRIMARY_KEYS]) | set(meta[self.REPLICATION_KEYS])

        for record in records_written:
            with self.subTest(stream=stream_name):
                for field in required_fields:
                    self.assertIn(
                        field, record,
                        msg=f"Automatic field '{field}' missing from {stream_name} record",
                    )

    def test_ads_pk_present_in_records(self):
        written = self._sync_stream_minimal("ads", "Ads", [{"id": 42, "ad_type": "Banner"}])
        self.assertGreater(len(written), 0)
        self._assert_automatic_fields_present("ads", written)

    def test_deals_pk_present_in_records(self):
        written = self._sync_stream_minimal("deals", "Deals", [{"id": 99, "name": "Big Deal"}])
        self.assertGreater(len(written), 0)
        self._assert_automatic_fields_present("deals", written)

    def test_phone_numbers_pk_present(self):
        written = self._sync_stream_minimal(
            "phone_numbers", "PhoneNumbers", [{"id": 5, "phone_number": "+15555550100"}]
        )
        self.assertGreater(len(written), 0)
        self._assert_automatic_fields_present("phone_numbers", written)

    def test_company_information_pk_present(self):
        written = self._sync_stream_minimal(
            "company_information",
            "CompanyInformation",
            [{"company_name": "Acme Corp"}],
            id_fields=["company_name"],
        )
        self.assertGreater(len(written), 0)
        self._assert_automatic_fields_present("company_information", written)

    def test_invoices_pk_and_rep_key_present(self):
        written = self._sync_stream_minimal(
            "invoices",
            "Invoices",
            [{"id": 1, "created_date": "2024-01-01T00:00:00Z"}],
            bookmark_field="created_date",
            bookmark_type="datetime",
        )
        self.assertGreater(len(written), 0)
        self._assert_automatic_fields_present("invoices", written)

    def test_api_submissions_pk_and_rep_key_present(self):
        written = self._sync_stream_minimal(
            "api_submissions",
            "APISubmission",
            [{"batch_id": "B001", "submission_date": "2024-01-01T00:00:00Z"}],
            bookmark_field="submission_date",
            bookmark_type="datetime",
            id_fields=["batch_id"],
        )
        self.assertGreater(len(written), 0)
        self._assert_automatic_fields_present("api_submissions", written)

    def test_ftp_submissions_pk_and_rep_key_present(self):
        written = self._sync_stream_minimal(
            "ftp_file_submissions",
            "FTPFileSubmissions",
            [{"batch_id": "FTP1", "submission_date": "2024-03-01T00:00:00Z"}],
            bookmark_field="submission_date",
            bookmark_type="datetime",
            id_fields=["batch_id"],
        )
        self.assertGreater(len(written), 0)
        self._assert_automatic_fields_present("ftp_file_submissions", written)

    def test_automatic_fields_present_on_all_records(self):
        """All records in a batch must carry the automatic fields."""
        records = [{"id": i, "created_date": "2024-01-01T00:00:00Z"} for i in range(1, 6)]
        written = self._sync_stream_minimal(
            "invoices",
            "Invoices",
            records,
            bookmark_field="created_date",
            bookmark_type="datetime",
        )
        self.assertEqual(len(written), 5)
        self._assert_automatic_fields_present("invoices", written)
