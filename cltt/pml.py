"""Loading and saving CLTT PML XML files."""

import logging
import re

from collections import defaultdict


def put_entities_into_m_files(detected_entities, accounting_dictionary, pml_input_filepath, pml_output_filepath):
    """Load the M-file, append entities annotation, save the file."""

    # Index detected entities according to the node_id.
    node2entity_id = dict()
    for entity in detected_entities:
        for node_id in entity['node_ids']:
            node2entity_id[node_id] = entity

    # Read M file and change identifiers according to mapping
    with open(pml_input_filepath, 'r') as m_file_input:
        with open(pml_output_filepath, 'w') as m_file_output:
            for line in m_file_input:
                m_file_output.write(line)

                m_node_match = re.match(r'\s*<m id="m-(?P<node_id>.*)">', line)
                if m_node_match:
                    node_id = m_node_match.group('node_id')
                    if node_id in node2entity_id:
                        cltt_annotation = []
                        cltt_annotation.append("      <cltt_entity_id>%s</cltt_entity_id>\n" % node2entity_id[node_id]['entity_id'])
                        cltt_annotation.append("      <cltt_entity_type>%s</cltt_entity_type>\n" % node2entity_id[node_id]['entity_type'])
                        cltt_annotation.append("      <cltt_entity_dictionary_id>%s</cltt_entity_dictionary_id>\n" % node2entity_id[node_id]['dictionary_id'])
                        cltt_annotation.append("      <cltt_entity_dictionary_form>%s</cltt_entity_dictionary_form>\n" % accounting_dictionary.dictionary[node2entity_id[node_id]['dictionary_id']]['entity_form'])
                        line = ''.join(cltt_annotation)
                        line = line.encode('utf8')
                        m_file_output.write(line)


def _find_root_node(dictionary_entry):
    for node_index in range(len(dictionary_entry['dependency_tree'])):
        if dictionary_entry['dependency_tree'][node_index]['parent'] == 0:
            return node_index


def put_relations_into_m_files(relations, accounting_dictionary, pml_input_filepath, pml_output_filepath):
    """Load the M-file, append relations annotation, save the file."""

    relation_data = defaultdict(list)

    for relation in relations:
        # Subject nodes data.
        for node_id in relation['subject']['node_ids']:
            dictionary_entry = accounting_dictionary.dictionary[relation['object']['dictionary_id']]
            root_object_node = _find_root_node(dictionary_entry)
            relation_data[node_id].append({
                'id': relation['relation_id'],
                'type': relation['relation_type'],
                'subpart': 'subject',
                'subject': '',
                'predicate': relation['predicate']['node_ids'][0],
                'object': relation['object']['node_ids'][root_object_node]
            })

        # Predicate nodes data.
        for node_id in relation['predicate']['node_ids']:
            dictionary_entry = accounting_dictionary.dictionary[relation['subject']['dictionary_id']]
            root_subject_node = _find_root_node(dictionary_entry)

            dictionary_entry = accounting_dictionary.dictionary[relation['object']['dictionary_id']]
            root_object_node = _find_root_node(dictionary_entry)

            relation_data[node_id].append({
                'id': relation['relation_id'],
                'type': relation['relation_type'],
                'subpart': 'predicate',
                'subject': relation['subject']['node_ids'][root_subject_node],
                'predicate': '',
                'object': relation['object']['node_ids'][root_object_node]
            })

        # Object nodes data.
        for node_id in relation['object']['node_ids']:
            dictionary_entry = accounting_dictionary.dictionary[relation['subject']['dictionary_id']]
            root_subject_node = _find_root_node(dictionary_entry)

            relation_data[node_id].append({
                'id': relation['relation_id'],
                'type': relation['relation_type'],
                'subpart': 'object',
                'subject': relation['subject']['node_ids'][root_subject_node],
                'predicate': relation['predicate']['node_ids'][0],
                'object': ''
            })

    # Read M file and change identifiers according to mapping
    with open(pml_input_filepath, 'r') as m_file_input:
        with open(pml_output_filepath, 'w') as m_file_output:
            for line in m_file_input:
                m_file_output.write(line)

                m_node_match = re.match(r'\s*<m id="m-(?P<node_id>.*)">', line)
                if m_node_match:
                    node_id = m_node_match.group('node_id')
                    if relation_data[node_id]:
                        cltt_annotation = []
                        cltt_annotation.append("      <cltt_relations>\n")

                        for relation in relation_data[node_id]:
                            cltt_annotation.append("         <cltt_relation>\n")
                            cltt_annotation.append("             <cltt_relation_id>%s</cltt_relation_id>\n" % relation['id'])
                            cltt_annotation.append("             <cltt_relation_type>%s</cltt_relation_type>\n" % relation['type'])
                            cltt_annotation.append("             <cltt_relation_subpart>%s</cltt_relation_subpart>\n" % relation['subpart'])
                            cltt_annotation.append("             <cltt_relation_subject_reference>%s</cltt_relation_subject_reference>\n" % relation['subject'])
                            cltt_annotation.append("             <cltt_relation_predicate_reference>%s</cltt_relation_predicate_reference>\n" % relation['predicate'])
                            cltt_annotation.append("             <cltt_relation_object_reference>%s</cltt_relation_object_reference>\n" % relation['object'])
                            cltt_annotation.append("         </cltt_relation>\n")

                        cltt_annotation.append("      </cltt_relations>\n")

                        line = ''.join(cltt_annotation)
                        line = line.encode('utf8')
                        m_file_output.write(line)


def load_m_file(pml_m_filepath):
    """Load CLTT sentences from the PML M file."""

    file_name_match = re.match(r'.*/?(?P<document_id>document_0[12]_00\d).m$', pml_m_filepath)
    if not file_name_match:
        raise ValueError('Invalid PML M filename %s' % pml_m_filepath)

    document_id = file_name_match.group('document_id')
    char_offset = 0
    sentences = list()
    tokens_offsets = dict()

    with open(pml_m_filepath, 'r') as pml_data:
        tokens = []
        node_id = None
        node_form = None

        for line in pml_data:
            line = line.decode('utf-8')
            logging.debug('Input line = %s', line)

            sentence_match = re.match(r'\s*<s .*', line)
            if sentence_match:
                if tokens:
                    logging.debug('Sentence end. Number of nodes: %d. Offset: %d', len(tokens), char_offset)
                    logging.debug('')
                    char_offset += 1
                    sentences.append(list(tokens))
                tokens = []

            node_id_match = re.match(r"\s*<m id=[\"']m-(a-)?(?P<node_id>.*)[\"']>", line)
            if node_id_match:
                node_id = node_id_match.group('node_id')
                logging.debug('Extracted node id = %s', node_id)

            node_form_match = re.match(r"\s*<form>(?P<node_form>.*)</form>", line)
            if node_form_match:
                node_form = node_form_match.group('node_form')
                logging.debug('Extracted node form = %s', node_form)

            if node_id and node_form:
                start_offset = char_offset if not tokens else char_offset + 1
                end_offset = start_offset + len(node_form)
                char_offset = end_offset
                tokens.append({'node_id': node_id, 'node_form': node_form, 'start_offset': start_offset, 'end_offset': end_offset})
                tokens_offsets[node_id] = {'form': node_form, 'start': start_offset, 'end': end_offset}
                logging.debug('%20s | %10d | %10d', node_form, start_offset, end_offset)
                node_id = None
                node_form = None

        if tokens:
            sentences.append(tokens)

    logging.info('Loaded %d sentences from document %s', len(sentences), document_id)
    document = {
        'document_id': document_id,
        'sentences': sentences,
        'token_offsets': tokens_offsets
    }

    return document
