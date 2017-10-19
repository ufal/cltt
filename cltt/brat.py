"""Importing and exporting CLTT manual annotation for the Brat annotation tool."""

import logging
import re


def load_ann_file(brat_ann_file):
    """Load Brat ANN files with entities and relations."""

    file_name_match = re.match(r'.*/?(?P<document_id>document_0[12]_00\d).ann$', brat_ann_file)
    if not file_name_match:
        raise ValueError('Invalid Brat ANN filename %s' % brat_ann_file)

    document_id = file_name_match.group('document_id')
    entities = []
    relations = []

    with open(brat_ann_file, 'r') as input_file:
        for line in input_file:
            line = line.rstrip()

            if line[0] == 'T':
                entity_id, annotation, text = line.split('\t')
                entity_type, start_offset, end_offset = annotation.split(' ')
                entities.append({
                    'document_id': document_id,
                    'id': entity_id,
                    'type': entity_type,
                    'start': int(start_offset),
                    'end': int(end_offset),
                    'text': text
                })

            elif line[0] == 'R':
                relation_id, arguments = line.split('\t')
                relation_type, arg1, arg2 = arguments.split(' ')
                arg1 = re.sub(r'Arg1:', '', arg1)
                arg2 = re.sub(r'Arg2:', '', arg2)
                relations.append({
                    'document_id': document_id,
                    'id': relation_id,
                    'type': relation_type,
                    'arg1': arg1,
                    'arg2': arg2
                })

            else:
                logging.warning('Unknown line %s', line)

        logging.info('Loaded %d manually annotated entities from %s document.', len(entities), document_id)
        logging.info('Loaded %d manually annotated relations from %s document.', len(relations), document_id)

    return entities, relations


def create_plaintext_files(documents, brat_dir):
    for document in documents:
        document_id = document['document_id']
        full_path = '/'.join([brat_dir, document_id + '.txt'])
        with open(full_path, 'w') as output_file:
            for sentence in document['sentences']:
                line = ' '.join(token['node_form'] for token in sentence)
                output_file.write(line.encode('utf8'))
                output_file.write('\n')


def create_annotation_files(documents, node_offsets, entities, dictionary, brat_dir):
    for document in documents:
        document_id = document['document_id']
        full_path = '/'.join([brat_dir, document_id + '.ann'])
        with open(full_path, 'w') as output_file:
            entity_counter = 0
            sorted_entities = sorted(entities, key=lambda entity:node_offsets[entity['start_node']]['start'])
            for entity in sorted_entities:
                if entity['document_id'] != document_id:
                    continue

                entity_counter += 1
                entity_ord = 'T%d' % entity_counter
                entity_type = dictionary[entity['entity_id']]
                start_offest = node_offsets[entity['start_node']]['start']
                end_offset = node_offsets[entity['end_node']]['end']
                entity_form = ' '.join([node_offsets[node]['form'] for node in entity['nodes']])
                chunk_triple = '%s %d %d' % (entity_type, start_offest, end_offset)
                line = '\t'.join([entity_ord, chunk_triple, entity_form])
                output_file.write(line.encode('utf8'))
                output_file.write('\n')
