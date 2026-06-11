"""Base class for tap-impact mock integration tests."""
import json
import os


class ImpactBaseTest:
    """Base test mixin for tap-impact mock integration tests.

    Provides stream metadata, mock config, and schema-driven record generation.
    """

    PRIMARY_KEYS = "primary_keys"
    REPLICATION_METHOD = "replication_method"
    REPLICATION_KEYS = "replication_keys"
    OBEYS_START_DATE = "obeys_start_date"
    API_LIMIT = "api_limit"
    PARENT = "parent"

    default_start_date = "2020-01-01T00:00:00Z"

    def setUp(self):
        """Set up test fixtures."""
        self.config = self.get_mock_config()
        self.state = {}

    def tearDown(self):
        pass

    @staticmethod
    def get_mock_config():
        """Dummy configuration values — no real credentials."""
        return {
            "account_sid": "mock_account_sid",
            "auth_token": "mock_auth_token",
            "api_catalog": "Advertisers",
            "start_date": "2020-01-01T00:00:00Z",
            "user_agent": "tap-impact/mock-test",
        }

    @staticmethod
    def get_mock_state():
        return {}

    @classmethod
    def expected_metadata(cls):
        """Expected streams and metadata."""
        return {
            "ads": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "api_submissions": {
                cls.PRIMARY_KEYS: {"batch_id"},
                cls.REPLICATION_METHOD: "INCREMENTAL",
                cls.REPLICATION_KEYS: {"submission_date"},
                cls.OBEYS_START_DATE: True,
                cls.API_LIMIT: 100,
            },
            "campaigns": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "actions": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "INCREMENTAL",
                cls.REPLICATION_KEYS: {"event_date"},
                cls.OBEYS_START_DATE: True,
                cls.API_LIMIT: 100,
            },
            "action_inquiries": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "INCREMENTAL",
                cls.REPLICATION_KEYS: {"creation_date"},
                cls.OBEYS_START_DATE: True,
                cls.API_LIMIT: 100,
            },
            "action_updates": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "INCREMENTAL",
                cls.REPLICATION_KEYS: {"update_date"},
                cls.OBEYS_START_DATE: True,
                cls.API_LIMIT: 100,
            },
            "contacts": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
                cls.PARENT: "campaigns",
            },
            "conversion_paths": {
                cls.PRIMARY_KEYS: {"uri"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "media_partner_groups": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
                cls.PARENT: "campaigns",
            },
            "notes": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "INCREMENTAL",
                cls.REPLICATION_KEYS: {"modification_date"},
                cls.OBEYS_START_DATE: True,
                cls.API_LIMIT: 100,
                cls.PARENT: "campaigns",
            },
            "catalogs": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "catalog_items": {
                cls.PRIMARY_KEYS: {"catalog_item_id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
                cls.PARENT: "catalogs",
            },
            "company_information": {
                cls.PRIMARY_KEYS: {"company_name"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 1,
            },
            "deals": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "exception_lists": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "exception_list_items": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "ftp_file_submissions": {
                cls.PRIMARY_KEYS: {"batch_id"},
                cls.REPLICATION_METHOD: "INCREMENTAL",
                cls.REPLICATION_KEYS: {"submission_date"},
                cls.OBEYS_START_DATE: True,
                cls.API_LIMIT: 100,
            },
            "invoices": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "INCREMENTAL",
                cls.REPLICATION_KEYS: {"created_date"},
                cls.OBEYS_START_DATE: True,
                cls.API_LIMIT: 100,
            },
            "media_partners": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "phone_numbers": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "promo_codes": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "reports": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "report_metadata": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "tracking_value_requests": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
            "unique_urls": {
                cls.PRIMARY_KEYS: {"id"},
                cls.REPLICATION_METHOD: "FULL_TABLE",
                cls.REPLICATION_KEYS: set(),
                cls.OBEYS_START_DATE: False,
                cls.API_LIMIT: 100,
            },
        }

    @classmethod
    def expected_stream_names(cls):
        return set(cls.expected_metadata().keys())

    @classmethod
    def incremental_streams(cls):
        return {
            s for s, m in cls.expected_metadata().items()
            if m[cls.REPLICATION_METHOD] == "INCREMENTAL"
        }

    @classmethod
    def full_table_streams(cls):
        return {
            s for s, m in cls.expected_metadata().items()
            if m[cls.REPLICATION_METHOD] == "FULL_TABLE"
        }

    @staticmethod
    def _schema_path(stream_name):
        base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        return os.path.join(base_dir, "tap_impact", "schemas", f"{stream_name}.json")

    @classmethod
    def _load_schema(cls, stream_name):
        with open(cls._schema_path(stream_name), "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _schema_type(schema):
        t = schema.get("type", "object")
        if isinstance(t, list):
            non_null = [x for x in t if x != "null"]
            return non_null[0] if non_null else "null"
        return t

    @staticmethod
    def _generate_value(schema, date_value="2024-01-01T00:00:00Z"):
        if "enum" in schema and schema["enum"]:
            return schema["enum"][0]
        # Handle anyOf: pick first non-null sub-schema, or return None
        if "anyOf" in schema:
            for sub in schema["anyOf"]:
                if sub.get("type") != "null":
                    return ImpactBaseTest._generate_value(sub, date_value)
            return None
        schema_type = ImpactBaseTest._schema_type(schema)
        if schema_type == "object":
            return {
                key: ImpactBaseTest._generate_value(val, date_value)
                for key, val in schema.get("properties", {}).items()
            }
        if schema_type == "array":
            return [ImpactBaseTest._generate_value(
                schema.get("items", {"type": "string"}), date_value)]
        if schema_type == "string":
            fmt = schema.get("format")
            if fmt == "date-time":
                return date_value
            if fmt == "email":
                return "mock@example.com"
            return "mock"
        return {"integer": 1, "number": 1.0, "boolean": True}.get(schema_type)

    @classmethod
    def _generate_stream_record(cls, stream_name, date_value="2024-01-01T00:00:00Z"):
        """Generate one schema-valid mock record for the given stream (snake_case keys)."""
        return cls._generate_value(cls._load_schema(stream_name), date_value=date_value)


