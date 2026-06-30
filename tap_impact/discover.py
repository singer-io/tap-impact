import singer
from singer.catalog import Catalog, CatalogEntry, Schema
from tap_impact.client import ImpactForbiddenError
from tap_impact.schema import get_schemas
from tap_impact.streams import STREAMS, flatten_streams

LOGGER = singer.get_logger()


def _get_child_to_parent_map():
    """Returns a mapping of child stream name -> parent stream name."""
    mapping = {}
    for parent_name, parent_config in STREAMS.items():
        for child_name in parent_config.get('children', {}):
            mapping[child_name] = parent_name
    return mapping


def _check_stream_access(client, stream_name, path):
    """Return True if the stream is accessible, False if 403 Forbidden."""
    try:
        client.request('GET', path=path, params={'PageSize': 1}, endpoint=stream_name)
        return True
    except ImpactForbiddenError as ex:
        LOGGER.warning(
            "Excluding unauthorized stream '%s' from catalog. HTTP-Error-Message: '%s'",
            stream_name,
            str(ex)
        )
        return False


def _prune_inaccessible_children(schemas, field_metadata, child_to_parent):
    """Remove child streams from the catalog whose parent stream was excluded."""
    for child_name, parent_name in child_to_parent.items():
        if child_name in schemas and parent_name not in schemas:
            LOGGER.warning(
                "Stream '%s' excluded from catalog because its parent stream '%s' is not accessible.",
                child_name, parent_name,
            )
            schemas.pop(child_name)
            field_metadata.pop(child_name)


def _apply_access_checks(client, schemas, field_metadata):
    """
    Probe each parent stream for read access and remove inaccessible streams
    (and their children) from schemas and field_metadata in place.
    Raises ImpactForbiddenError if no parent streams are accessible.
    """
    inaccessible_streams = [
        stream_name
        for stream_name, stream_config in STREAMS.items()
        if stream_name in schemas
        and not _check_stream_access(client, stream_name, stream_config['path'])
    ]

    for stream_name in inaccessible_streams:
        schemas.pop(stream_name, None)
        field_metadata.pop(stream_name, None)

    child_to_parent = _get_child_to_parent_map()
    _prune_inaccessible_children(schemas, field_metadata, child_to_parent)

    accessible_streams = [s for s in STREAMS if s in schemas]

    if not accessible_streams:
        raise ImpactForbiddenError(
            "HTTP-error-code: 403, Error: The credentials do not have "
            "'read' access to any supported streams."
        )
    elif inaccessible_streams:
        LOGGER.warning(
            "No 'read' access to stream(s): %s. Excluded from catalog.",
            ", ".join(inaccessible_streams),
        )


def discover(client, config):
    """
    Run the discovery mode, prepare the catalog and return it.
    Access to each parent stream is verified using the provided client and
    streams the credentials cannot read are excluded from the returned catalog.
    """
    model_id = config.get('model_id')
    schemas, field_metadata = get_schemas()
    _apply_access_checks(client, schemas, field_metadata)
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
