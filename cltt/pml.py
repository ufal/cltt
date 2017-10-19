"""Loading and saving CLTT PML XML files."""

import logging
import re


def put_entities_into_m_files(detected_entities, pml_input_filepath, pml_output_filepath):
    """Load the M-file, append entities annotation, save the file."""

    node2entity_id = dict()
    for entity in detected_entities:
        for node_id in entity['node_ids']:
            node2entity_id[node_id] = {'entity_id': entity['entity_id'], 'entity_type': entity['entity_type']}

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
                        m_file_output.write(''.join(cltt_annotation))


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

            sentence_match = re.match(r'^\s+<s .*', line)
            if sentence_match:
                if tokens:
                    logging.debug('Sentence end. Number of nodes: %d. Offset: %d', len(tokens), char_offset)
                    logging.debug('')
                    char_offset += 1
                    sentences.append(list(tokens))
                tokens = []

            node_id_match = re.match(r'^\s+<m id="m-(?P<node_id>.*)">', line)
            if node_id_match:
                node_id = node_id_match.group('node_id')

            node_form_match = re.match(r'^\s+<form>(?P<node_form>.*)</form>', line)
            if node_form_match:
                node_form = node_form_match.group('node_form')

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

    logging.info('Loaded %4d sentences from document %s', len(sentences), document_id)
    document = {
        'document_id': document_id,
        'sentences': sentences,
        'token_offsets': tokens_offsets
    }

    return document
