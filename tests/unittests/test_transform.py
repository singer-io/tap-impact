"""Unit tests for tap_impact.transform module."""
import unittest
from tap_impact.transform import (
    convert,
    convert_array,
    convert_json,
    replace_order_id,
    transform_conversion_paths,
    transform_json,
)


class TestConvert(unittest.TestCase):
    """Tests for camelCase-to-snake_case conversion."""

    def test_simple_camel_case(self):
        self.assertEqual(convert("camelCase"), "camel_case")

    def test_multi_word_camel_case(self):
        self.assertEqual(convert("campaignId"), "campaign_id")

    def test_pascal_case(self):
        self.assertEqual(convert("CampaignId"), "campaign_id")

    def test_already_snake_case(self):
        self.assertEqual(convert("already_snake"), "already_snake")

    def test_acronym_handling(self):
        # regex treats 'API' as a single uppercase word before 'Submission'
        self.assertEqual(convert("APISubmission"), "api_submission")

    def test_single_word_lowercase(self):
        self.assertEqual(convert("id"), "id")

    def test_single_word_uppercase(self):
        # All-caps single word — regex does not insert underscore between capitals at end
        self.assertEqual(convert("ID"), "id")

    def test_empty_string(self):
        self.assertEqual(convert(""), "")

    def test_multiple_capitals_in_sequence(self):
        # e.g. "MediaURL" → "media_u_r_l" (standard regex behaviour)
        result = convert("MediaURL")
        self.assertIsInstance(result, str)
        self.assertEqual(result, result.lower())


class TestConvertArray(unittest.TestCase):
    """Tests for convert_array()."""

    def test_flat_string_list(self):
        self.assertEqual(convert_array(["a", "b"]), ["a", "b"])

    def test_dict_in_array(self):
        result = convert_array([{"camelKey": "value"}])
        self.assertEqual(result, [{"camel_key": "value"}])

    def test_nested_list_in_array(self):
        result = convert_array([["a", "b"]])
        self.assertEqual(result, [["a", "b"]])

    def test_nested_dict_in_list_in_array(self):
        result = convert_array([[{"nestedKey": 1}]])
        self.assertEqual(result, [[{"nested_key": 1}]])

    def test_mixed_types(self):
        result = convert_array([1, "str", {"keyName": "val"}])
        self.assertEqual(result, [1, "str", {"key_name": "val"}])

    def test_empty_array(self):
        self.assertEqual(convert_array([]), [])


class TestConvertJson(unittest.TestCase):
    """Tests for convert_json()."""

    def test_simple_key(self):
        self.assertEqual(convert_json({"myKey": 1}), {"my_key": 1})

    def test_nested_dict(self):
        result = convert_json({"outerKey": {"innerKey": "val"}})
        self.assertEqual(result, {"outer_key": {"inner_key": "val"}})

    def test_list_value(self):
        result = convert_json({"myList": [{"itemKey": 1}]})
        self.assertEqual(result, {"my_list": [{"item_key": 1}]})

    def test_scalar_value_unchanged(self):
        result = convert_json({"myNum": 42})
        self.assertEqual(result, {"my_num": 42})

    def test_empty_dict(self):
        self.assertEqual(convert_json({}), {})

    def test_multiple_keys(self):
        result = convert_json({"firstName": "John", "lastName": "Doe"})
        self.assertEqual(result, {"first_name": "John", "last_name": "Doe"})


class TestReplaceOrderId(unittest.TestCase):
    """Tests for replace_order_id()."""

    def test_oid_replaced_with_order_id(self):
        data = {"Actions": [{"oid": "O123", "amount": 10.0}]}
        result = replace_order_id(data, "Actions")
        self.assertEqual(result["Actions"][0]["order_id"], "O123")
        self.assertNotIn("oid", result["Actions"][0])

    def test_missing_oid_replaced_with_none(self):
        data = {"Actions": [{"amount": 10.0}]}
        result = replace_order_id(data, "Actions")
        self.assertIsNone(result["Actions"][0]["order_id"])
        self.assertNotIn("oid", result["Actions"][0])

    def test_multiple_records(self):
        data = {"Actions": [{"oid": "O1"}, {"oid": "O2"}]}
        result = replace_order_id(data, "Actions")
        self.assertEqual(result["Actions"][0]["order_id"], "O1")
        self.assertEqual(result["Actions"][1]["order_id"], "O2")

    def test_empty_records(self):
        data = {"Actions": []}
        result = replace_order_id(data, "Actions")
        self.assertEqual(result["Actions"], [])


class TestTransformConversionPaths(unittest.TestCase):
    """Tests for transform_conversion_paths()."""

    def _make_data(self, events, referral_counts=None):
        record = {"events": events}
        if referral_counts is not None:
            record["referral_counts"] = referral_counts
        return {"ConversionPaths": [record]}

    def test_events_as_list(self):
        data = self._make_data([{"oid": "O1", "type": "click"}])
        result = transform_conversion_paths(data, "ConversionPaths")
        events = result["ConversionPaths"][0]["events"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["order_id"], "O1")
        self.assertNotIn("oid", events[0])

    def test_events_as_dict_wrapping_event(self):
        data = self._make_data({"event": {"oid": "O2", "type": "sale"}})
        result = transform_conversion_paths(data, "ConversionPaths")
        events = result["ConversionPaths"][0]["events"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["order_id"], "O2")

    def test_events_none(self):
        data = {"ConversionPaths": [{}]}
        result = transform_conversion_paths(data, "ConversionPaths")
        self.assertEqual(result["ConversionPaths"][0]["events"], [])

    def test_referral_counts_as_list(self):
        data = self._make_data([], [{"count": 5}])
        result = transform_conversion_paths(data, "ConversionPaths")
        self.assertEqual(result["ConversionPaths"][0]["referral_counts"], [{"count": 5}])

    def test_referral_counts_as_dict(self):
        data = self._make_data([], {"referral_count": {"count": 3}})
        result = transform_conversion_paths(data, "ConversionPaths")
        rc = result["ConversionPaths"][0]["referral_counts"]
        self.assertEqual(len(rc), 1)
        self.assertEqual(rc[0]["count"], 3)

    def test_event_without_oid(self):
        data = self._make_data([{"type": "impression"}])
        result = transform_conversion_paths(data, "ConversionPaths")
        events = result["ConversionPaths"][0]["events"]
        self.assertIsNone(events[0]["order_id"])


class TestTransformJson(unittest.TestCase):
    """Tests for transform_json() — high-level integration of transforms."""

    def test_actions_stream_replaces_oid(self):
        raw = {"Actions": [{"oid": "O99", "eventDate": "2024-01-01"}]}
        result = transform_json(raw, "actions", "Actions")
        self.assertEqual(result[0]["order_id"], "O99")
        self.assertNotIn("oid", result[0])

    def test_action_updates_stream_replaces_oid(self):
        raw = {"ActionUpdates": [{"oid": "U10", "updateDate": "2024-01-02"}]}
        result = transform_json(raw, "action_updates", "ActionUpdates")
        self.assertEqual(result[0]["order_id"], "U10")

    def test_conversion_paths_stream_transforms_events(self):
        raw = {
            "ConversionPaths": [{
                "events": [{"oid": "E1", "type": "click"}],
                "referral_counts": []
            }]
        }
        result = transform_json(raw, "conversion_paths", "ConversionPaths")
        self.assertEqual(result[0]["events"][0]["order_id"], "E1")

    def test_other_stream_converts_camel_case(self):
        raw = {"Campaigns": [{"campaignId": 1, "campaignName": "Test"}]}
        result = transform_json(raw, "campaigns", "Campaigns")
        self.assertEqual(result[0]["campaign_id"], 1)
        self.assertEqual(result[0]["campaign_name"], "Test")

    def test_returns_list(self):
        raw = {"Ads": [{"id": 1}]}
        result = transform_json(raw, "ads", "Ads")
        self.assertIsInstance(result, list)
