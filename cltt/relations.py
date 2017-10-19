"""Methods for processing CLTT Semantic Relations."""

import json
import logging
import re


class RelationBuilder(object):
    """Build CLTT Semantic Entities from the Brat manual annotations."""

    def __init__(self, annotated_relations, annotated_entities, detected_entities, document):
        self.annotated_relations = annotated_relations
        self.annotated_entities = annotated_entities
        self.detected_entities = detected_entities
        self.document = document

        self.relations = []
        self.predicate_entities = None
        self.annotated_to_detected_mapping = None

    def align_entities(self):
        """Identify which automatically detected entity is aligned to manually annotated one."""

        self.annotated_to_detected_mapping = dict()
        self.predicate_entities = dict()

        for annotated_entity in self.annotated_entities:
            logging.debug('\n\n')
            logging.debug('Processing manual entity %r', annotated_entity)
            annotated_entity_id = annotated_entity['id']

            if annotated_entity['type'] in ['Definition', 'Obligation', 'Right']:
                self.predicate_entities[annotated_entity_id] = annotated_entity
                logging.debug(' --> relation')
                continue

            for detected_entity in self.detected_entities:
                detected_entity_id = detected_entity['entity_id']
                if annotated_entity['start'] != detected_entity['text_chunk_start_offset']:
                    continue

                if annotated_entity['end'] != detected_entity['text_chunk_end_offset']:
                    continue

                logging.debug(' --> entity %s', detected_entity['dictionary_id'])
                self.annotated_to_detected_mapping[annotated_entity_id] = detected_entity_id

    def get_annotated_entity(self, entity_id):
        """Find annotated entity with the specified ID."""

        for entity in self.annotated_entities:
            if entity['id'] == entity_id:
                return entity

    def get_detected_entity(self, entity_id):
        """Find detected entity with the specified ID."""

        for entity in self.detected_entities:
            if entity['entity_id'] == entity_id:
                return entity

    def find_objects(self, predicate_id):
        """Find all objects that with specified predicate."""

        objects = []
        for relation in self.annotated_relations:
            if relation['type'] == 'obj' and relation['arg1'] == predicate_id:
                entity = self.get_annotated_entity(relation['arg2'])
                objects.append(entity)
        return objects

    @staticmethod
    def print_relation(relation):
        subject = '%s (%s)' % (relation['subject']['text'], relation['subject']['type'])
        predicate = '%s (%s)' % (relation['predicate']['text'], relation['predicate']['type'])
        object = '%s (%s)' % (relation['object']['text'], relation['object']['type'])
        logging.info('%s - %s - %s', subject, predicate, object)

    def identify_predicate_nodes(self, predicate_annotated_entity):
        """Determine nodes for predicate entities."""

        for sentence in self.document['sentences']:
            for node in sentence:
                if node['start_offset'] != predicate_annotated_entity['start']:
                    continue

                if node['end_offset'] != predicate_annotated_entity['end']:
                    continue

                return [node['node_id']]

    def build_relations(self):
        """Build CLTT semantic relations from the Brat annotations."""

        logging.info('')
        logging.info('Relation builder for %s', self.document['document_id'])

        self.relations = []
        relation_counter = 0

        for annotated_relation in self.annotated_relations:
            if annotated_relation['type'] != 'subj':
                continue

            logging.info('Processing Brat relation %r', annotated_relation)
            subject_annotated_entity_id = annotated_relation['arg2']
            predicate_annotated_entity_id = annotated_relation['arg1']

            # Find subject nad predicate in the annotatedly annotated data.
            subject_annotated_entity = self.get_annotated_entity(subject_annotated_entity_id)
            predicate_annotated_entity = self.get_annotated_entity(predicate_annotated_entity_id)
            object_annotated_entities = self.find_objects(predicate_annotated_entity_id)

            if not object_annotated_entities:
                logging.warning('No object for predicate %s', predicate_annotated_entity_id)

            # Find aligned automatically detected entities for each subject and object:
            for object_annotated_entity in object_annotated_entities:
                building_status = '!!'

                object_annotated_entity_id = object_annotated_entity['id']
                subject_detected_entity_id = self.annotated_to_detected_mapping.get(subject_annotated_entity_id, None)
                object_detected_entity_id = self.annotated_to_detected_mapping.get(object_annotated_entity_id, None)

                predicate_nodes = self.identify_predicate_nodes(predicate_annotated_entity)
                predicate_form = ' '.join([self.document['token_offsets'][node]['form'] for node in predicate_nodes])
                sentence_id = re.sub(r'.*(sentence\d+).*', '\\1', predicate_nodes[0])

                if subject_detected_entity_id and object_detected_entity_id:
                    relation_counter += 1
                    building_status = 'OK'

                    relation_id = '%s-entity%04d' % (self.document['document_id'], relation_counter)
                    relation_type = predicate_annotated_entity['type']

                    self.relations.append({
                        'relation_id': relation_id,
                        'relation_type': relation_type,
                        'document_id': self.document['document_id'],
                        'subject': self.get_detected_entity(subject_detected_entity_id),
                        'predicate': {
                            'node_ids': predicate_nodes,
                            'text_chunk_form': predicate_form.encode('utf8'),
                            'text_chunk_start_offset': self.document['token_offsets'][predicate_nodes[0]]['start'],
                            'text_chunk_end_offset': self.document['token_offsets'][predicate_nodes[-1]]['end']

                        },
                        'object': self.get_detected_entity(object_detected_entity_id)
                    })

                logging.info('')
                logging.info('(%s) Relation building:', building_status)
                logging.info(' - sentence  : %s', sentence_id)
                logging.info(' - subject   : %s', subject_annotated_entity['text'])
                logging.info('             : %s', subject_detected_entity_id)
                logging.info('             : %s', ', '.join(self.get_detected_entity(subject_detected_entity_id)['node_ids']) if subject_detected_entity_id else '')
                logging.info(' - predicate : %s', predicate_annotated_entity['text'])
                logging.info(' - object    : %s', object_annotated_entity['text'])
                logging.info('             : %s', object_detected_entity_id)
                logging.info('             : %s', ', '.join(self.get_detected_entity(object_detected_entity_id)['node_ids']) if object_detected_entity_id else '')

    def save_json(self, output_r_file):
        with open(output_r_file, 'w') as exported_json:
            json.dump(self.relations, exported_json, ensure_ascii=False)
