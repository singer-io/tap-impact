"""
Base test class for tap-impact integration tests (tap-tester).
"""
import os

from tap_tester.base_suite_tests.base_case import BaseCase


class ImpactBaseTest(BaseCase):
    """Setup expectations for tap-impact test sub classes.

    Metadata describing streams. Shared tap-specific methods (as needed).
    """

    start_date = "2020-01-01T00:00:00Z"
    PARENT = "parent"

    @staticmethod
    def tap_name():
        """The name of the tap."""
        return "tap-impact"

    @staticmethod
    def get_type():
        """The expected connection type in Stitch."""
        return "platform.impact"

    @classmethod
    def expected_metadata(cls):
        """The expected streams and metadata about the streams."""
        return {
            "ads": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "api_submissions": {
                cls.PRIMARY_KEYS: {"batch_id"},
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: {"submission_date"},
                cls.OBEYS_START_DATE: True,
                cls.API_LIMIT: 100,
            },
            "campaigns": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "actions": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: {"event_date"},
                cls.OBEYS_START_DATE: True,
                cls.API_LIMIT: 100,
                cls.PARENT: "campaigns",
            },
            "action_inquiries": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: {"creation_date"},
                cls.OBEYS_START_DATE: True,
                cls.API_LIMIT: 100,
                cls.PARENT: "campaigns",
            },
            "action_updates": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: {"update_date"},
                cls.OBEYS_START_DATE: True,
                cls.API_LIMIT: 100,
                cls.PARENT: "campaigns",
            },
            "contacts": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
                cls.PARENT: "campaigns",
            },
            "conversion_paths": {
                cls.PRIMARY_KEYS: {"uri"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
                cls.PARENT: "campaigns",
            },
            "media_partner_groups": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
                cls.PARENT: "campaigns",
            },
            "notes": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: {"modification_date"},
                cls.OBEYS_START_DATE: True,
                cls.API_LIMIT: 100,
                cls.PARENT: "campaigns",
            },
            "catalogs": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "catalog_items": {
                cls.PRIMARY_KEYS: {"catalog_item_id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
                cls.PARENT: "catalogs",
            },
            "company_information": {
                cls.PRIMARY_KEYS: {"company_name"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 1,
            },
            "deals": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "exception_lists": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "exception_list_items": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
                cls.PARENT: "exception_lists",
            },
            "ftp_file_submissions": {
                cls.PRIMARY_KEYS: {"batch_id"},
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: {"submission_date"},
                cls.OBEYS_START_DATE: True,
                cls.API_LIMIT: 100,
            },
            "invoices": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.INCREMENTAL,
                cls.REPLICATION_KEYS: {"created_date"},
                cls.OBEYS_START_DATE: True,
                cls.API_LIMIT: 100,
            },
            "media_partners": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "phone_numbers": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "promo_codes": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "reports": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "report_metadata": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
                cls.PARENT: "reports",
            },
            "tracking_value_requests": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "unique_urls": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: cls.FULL_TABLE,
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
        }

    @staticmethod
    def get_credentials():
        """Authentication information for the test account."""
        return {
            "account_sid": os.getenv("TAP_IMPACT_ACCOUNT_SID"),
            "auth_token": os.getenv("TAP_IMPACT_AUTH_TOKEN"),
        }

    def get_properties(self, original: bool = True):
        """Configuration of properties required for the tap."""
        return_value = {
            "start_date": self.start_date,
            "api_catalog": os.getenv("TAP_IMPACT_API_CATALOG", "Advertisers"),
            "user_agent": os.getenv("TAP_IMPACT_USER_AGENT", "tap-impact/integration-test"),
        }

        model_id = os.getenv("TAP_IMPACT_MODEL_ID")
        if model_id:
            return_value["model_id"] = model_id

        if original:
            return return_value

        return_value["start_date"] = self.start_date
        return return_value


