"""Tools for working with CLTT e-layer."""

import json
import logging
import re


def load_detected_entities(e_file):
    """Load CLTT entities."""

    with open(e_file, 'r') as e_file_data:
        entities = json.load(e_file_data)

        for entity in entities:
            entity['text_chunk_form'] = entity['text_chunk_form'].encode('utf8')

    return entities


def put_entities_into_json(document, detected_entities, accounting_dictionary, output_e_file):
    """Create a CLTT E FILE (i.e. JSON with description of entities)."""

    entities = []
    entity_counter = 0
    sorted_entities = sorted(detected_entities, key=lambda entity:document['token_offsets'][entity['start_node']]['start'])
    document_id = document['document_id']

    for entity in sorted_entities:
        entity_counter += 1
        entity_id = '%s-entity%04d' % (document_id, entity_counter)
        dictionary_id = entity['entity_id']
        entity_type = accounting_dictionary[entity['entity_id']]['entity_type']
        entity_form = ' '.join([document['token_offsets'][node]['form'] for node in entity['nodes']])

        exported_entity = {
            'entity_id': entity_id,
            'entity_type': entity_type,
            'document_id': document_id,
            'dictionary_id': dictionary_id,
            'node_ids': entity['nodes'],
            'text_chunk_form': entity_form.encode('utf8'),
            'text_chunk_start_offset': document['token_offsets'][entity['start_node']]['start'],
            'text_chunk_end_offset': document['token_offsets'][entity['end_node']]['end']
        }

        entities.append(exported_entity)

    with open(output_e_file, 'w') as exported_json:
        json.dump(entities, exported_json, ensure_ascii=False)


def filter_overlapping_entities(entities, document, accounting_dictionary):
    """Filter out entities that are included in more specific ones, i.e. they are completely included in other one."""

    filtered_entities = []
    for candidate_entity in sorted(entities, key=lambda entity: len(entity['nodes']), reverse=True):
        candidate_entity_nodes = set(candidate_entity['nodes'])

        exists_more_specific_entity = False
        for filtered_entity in filtered_entities:
            filtered_entities_nodes = set(filtered_entity['nodes'])
            if candidate_entity_nodes.issubset(filtered_entities_nodes):
                exists_more_specific_entity = True
                logging.debug('')
                logging.debug('Overlapping detection:')
                logging.debug(' - general entity  : %s (%s)', candidate_entity['entity_id'], accounting_dictionary.dictionary[candidate_entity['entity_id']]['entity_form'])
                logging.debug('                   : %s', ' '.join([document['token_offsets'][node]['form'] for node in candidate_entity['nodes']]))
                logging.debug('                   : %s', ' '.join(candidate_entity['nodes']))
                logging.debug(' - specific entity : %s (%s)', filtered_entity['entity_id'], accounting_dictionary.dictionary[filtered_entity['entity_id']]['entity_form'])
                logging.debug('                   : %s', ' '.join([document['token_offsets'][node]['form'] for node in filtered_entity['nodes']]))
                logging.debug('                   : %s', ' '.join(filtered_entity['nodes']))
                break

        if not exists_more_specific_entity:
            filtered_entities.append(candidate_entity)

    logging.info('Number of entities after overlapping filtering: %d', len(filtered_entities))
    return filtered_entities


def filter_fragmented_entities(entities, document, accounting_dictionary):
    """Filter out entities such that their tokens are not in a one token sequence."""

    filtered_entities = []
    for candidate_entity in entities:
        continuous_entity = True

        previous_ord = None
        for node in candidate_entity['nodes']:
            current_ord = int(re.sub(r'^.*node(\d+)$', r'\1', node))
            if previous_ord and current_ord != previous_ord + 1:
                continuous_entity = False
                break
            else:
                previous_ord = current_ord

        if continuous_entity:
            filtered_entities.append(candidate_entity)
        else:
            logging.debug('Fragmented entity : %s (%s)', candidate_entity['entity_id'], accounting_dictionary.dictionary[candidate_entity['entity_id']]['entity_form'])
            logging.debug('                  : %s', ' '.join([document['token_offsets'][node]['form'] for node in candidate_entity['nodes']]))

    logging.info('Number of entities after continuous control: %d', len(filtered_entities))
    return filtered_entities


