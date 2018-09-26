from elasticsearch_dsl import Search
from elasticsearch_dsl import HistogramFacet
from elasticsearch_dsl import TermsFacet

from data_explorer.util.reverse_nested_facet import ReverseNestedFacet
from flask import current_app


def get_field_type(es, field_name):
    # elasticsearch_dsl.Mapping, which gets mappings for all fields, would be
    # easier, but we can't use it.
    # BigQuery indexer uses field names like "project.dataset.table.column".
    # elasticsearch_dsl.Mapping corresponds to
    # "curl /index/_mapping/doc_type". That returns a nested dict:
    #   "project":
    #     "dataset":
    #       ...
    # It's difficult to retrieve type from the nested dict.
    # Instead, we get the type for one field:
    # "curl /index/_mapping/doc_type/project.dataset.table.column".
    # This has the benefit that we can support Elasticsearch documents that are
    # truly nested, such as HCA Orange Box. elasticsearch_field_name in ui.json
    # would be "parent.child".
    mapping = es.indices.get_field_mapping(
        fields=field_name,
        index=current_app.config['INDEX_NAME'],
        doc_type='type')

    if mapping == {}:
        raise ValueError(
            'elasticsearch_field_name %s not found in Elasticsearch index %s' %
            (field_name, current_app.config['INDEX_NAME']))

    # If field_name is "a.b.c", last_part is "c".
    last_part = field_name.split('.')[len(field_name.split('.')) - 1]
    return mapping[current_app.config['INDEX_NAME']]['mappings']['type'][
        field_name]['mapping'][last_part]['type']


def _get_field_min_max_agg(es, field_name):
    return Search(
        using=es, index=current_app.config['INDEX_NAME']
    ).aggs.metric(
        'max',
        'max',
        # Don't execute query; we only care about aggregations. See
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/returning-only-agg-results.html
        field=field_name
    ).params(size=0).aggs.metric(
        'min',
        'min',
        # Don't execute query; we only care about aggregations. See
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/returning-only-agg-results.html
        field=field_name).params(size=0).execute()


# TODO(bfcrampton): Generalize this for any nested field
def _get_samples_field_min_max_agg(es, field_name):
    search = Search(using=es, index=current_app.config['INDEX_NAME'])
    search.update_from_dict({
        "aggs": {
            "parent": {
                "nested": {
                    "path": "samples"
                },
                "aggs": {
                    "max": {
                        "max": {
                            "field": field_name
                        }
                    },
                    "min": {
                        "min": {
                            "field": field_name
                        }
                    }
                }
            }
        }
    })
    return search.params(size=0).execute()


def _get_field_range(es, field_name):
    if field_name.startswith('samples.'):
        response = _get_samples_field_min_max_agg(es, field_name)
    else:
        response = _get_field_min_max_agg(es, field_name)
    return (response.aggregations.parent['max']['value'] -
            response.aggregations.parent['min']['value'])


def _get_bucket_interval(field_range):
    if field_range <= 1:
        return .1
    if field_range < 8:
        return 1
    elif field_range < 20:
        return 2
    elif field_range < 150:
        # Make the ranges easy to read (10-19,20-29 instead of 10-17,18-25).
        return 10
    elif field_range < 1500:
        return 100
    elif field_range < 15000:
        return 1000
    elif field_range < 150000:
        return 10000
    elif field_range < 1500000:
        return 100000
    elif field_range < 15000000:
        return 1000000
    elif field_range < 150000000:
        return 10000000
    elif field_range < 1500000000:
        return 100000000
    elif field_range < 15000000000:
        return 1000000000
    elif field_range < 150000000000:
        return 10000000000
    elif field_range < 1500000000000:
        return 100000000000
    else:
        return 1000000000000


def get_elasticsearch_facet(es, elasticsearch_field_name, field_type):
    if field_type == 'text':
        # Use ".keyword" because we want aggregation on keyword field, not
        # term field. See
        # https://www.elastic.co/guide/en/elasticsearch/reference/6.2/fielddata.html#before-enabling-fielddata
        es_facet = TermsFacet(field=elasticsearch_field_name + '.keyword')

    elif field_type == 'boolean':
        es_facet = TermsFacet(field=elasticsearch_field_name)

    else:
        # Assume numeric type.
        # Creating this facet is a two-step process.
        # 1) Get max value
        # 2) Based on max value, determine bucket size. Create
        #    HistogramFacet with this bucket size.
        # TODO: When https://github.com/elastic/elasticsearch/issues/31828
        # is fixed, use AutoHistogramFacet instead. Will no longer need 2
        # steps.
        field_range = _get_field_range(es, elasticsearch_field_name)
        es_facet = HistogramFacet(
            field=elasticsearch_field_name,
            interval=_get_bucket_interval(field_range))

    # Handle sample facets in a special way since they are nested objects.
    if elasticsearch_field_name.startswith('samples.'):
        es_facet = ReverseNestedFacet('samples', es_facet)

    return es_facet