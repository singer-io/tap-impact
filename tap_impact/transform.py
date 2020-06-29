import re
import singer

LOGGER = singer.get_logger()

# Convert camelCase to snake_case
def convert(name):
    regsub = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', regsub).lower()


# Convert keys in json array
def convert_array(arr):
    new_arr = []
    for i in arr:
        if isinstance(i, list):
            new_arr.append(convert_array(i))
        elif isinstance(i, dict):
            new_arr.append(convert_json(i))
        else:
            new_arr.append(i)
    return new_arr


# Convert keys in json
def convert_json(this_json):
    out = {}
    for key in this_json:
        new_key = convert(key)
        if isinstance(this_json[key], dict):
            out[new_key] = convert_json(this_json[key])
        elif isinstance(this_json[key], list):
            out[new_key] = convert_array(this_json[key])
        else:
            out[new_key] = this_json[key]
    return out


# Replace system/reserved field 'oid' with 'order_id'
def replace_order_id(this_json, data_key):
    i = 0
    for record in this_json[data_key]:
        order_id = record.get('oid')
        this_json[data_key][i]['order_id'] = order_id
        this_json[data_key][i].pop('oid', None)
        i = i + 1
    return this_json


# Replace system/reserved field 'oid' with 'order_id' in nested events
# Also adjust events sub-node to always by a list/array (instead of array AND dict)
def transform_conversion_paths(this_json, data_key):
    i = 0
    for record in this_json[data_key]:
        events = record.get('events')
        events_list = []
        if isinstance(events, list):
            events_list = events
        elif isinstance(events, dict):
            event = events.get('event')
            events_list.append(event)
        this_json[data_key][i].pop('events', None)
        this_json[data_key][i]['events'] = []
        for event in events_list:
            if isinstance(event, dict):
                order_id = event.get('oid')
                event.pop('oid', None)
                event['order_id'] = order_id
                this_json[data_key][i]['events'].append(event)

        referral_counts = record.get('referral_counts')
        referral_counts_list = []
        if isinstance(referral_counts, list):
            referral_counts_list = referral_counts
        elif isinstance(referral_counts, dict):
            referral_count = referral_counts.get('referral_count')
            referral_counts_list.append(referral_count)
        this_json[data_key][i].pop('referral_counts', None)
        this_json[data_key][i]['referral_counts'] = []
        for referral_count in referral_counts_list:
            if isinstance(referral_count, dict):
                this_json[data_key][i]['referral_counts'].append(referral_count)

        i = i + 1
    return this_json


# Run all transforms: convert camelCase to snake_case for fieldname keys
def transform_json(this_json, stream_name, data_key):
    converted_json = convert_json(this_json)
    converted_data_key = convert(data_key)
    if stream_name in ('actions', 'action_updates'):
        transformed_json = replace_order_id(converted_json, converted_data_key)[converted_data_key]
    if stream_name in ['conversion_paths']:
        transformed_json = transform_conversion_paths(converted_json, converted_data_key)[converted_data_key]
    else:
        transformed_json = converted_json[converted_data_key]
    return transformed_json
