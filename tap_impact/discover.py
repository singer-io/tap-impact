from singer.catalog import Catalog, CatalogEntry, Schema
from tap_impact.schema import get_schemas
from tap_impact.streams import flatten_streams

def discover(config):
    model_id = config.get('model_id')
    schemas, field_metadata = get_schemas()
    catalog = Catalog([])

    flat_streams = flatten_streams()
    for stream_name, schema_dict in schemas.items():
        process_stream = True
        # conversion_paths endpoint requires model_id tap config param
        if stream_name == 'conversion_paths' and not model_id:
            process_stream = False
        if process_stream:
            schema = Schema.from_dict(schema_dict)
            mdata = field_metadata[stream_name]

            catalog.streams.append(CatalogEntry(
                stream=stream_name,
                tap_stream_id=stream_name,
                key_properties=flat_streams.get(stream_name, {}).get('key_properties', None),
                schema=schema,
                metadata=mdata
            ))

    return catalog
