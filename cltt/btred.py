"""Tools and utilities for working with BTRED."""

import logging
import re


def load_detected_entities(btred_filepath):
    """Load detected entities from the btred."""

    detected_entities = []

    file_name_match = re.match(r'.*/?(?P<document_id>document_0[12]_00\d).a-(?P<entity_id>\d+).txt', btred_filepath)
    if not file_name_match:
        raise ValueError('Could not parse %s filename.', btred_filepath)

    document_id = file_name_match.group('document_id')
    entity_id = file_name_match.group('entity_id')

    with open(btred_filepath, 'r') as bred_output:
        for line in bred_output:
            line = line.rstrip()

            node_ids = []
            for node_id in line.split('\t'):
                node_id = re.sub(r'^a-', '', node_id)
                node_ids.append(node_id)

            sentence_id = re.sub(r".*(sentence\d+).*", r"\1", node_ids[0])

            if node_ids:
                detected_entities.append({
                    'document_id': document_id,
                    'sentence_id': sentence_id,
                    'entity_id': entity_id,
                    'nodes': node_ids,
                    'start_node': node_ids[0],
                    'end_node': node_ids[-1]
                })

    return detected_entities
