"""Tools and data classes for manipulating with the Accounting Dictionary."""

import re
import logging
import json
from unidecode import unidecode


class Dictionary(object):
    """Dictionary representation."""

    def __init__(self):
        self.dictionary = None
        self.entity_types = None

    def load_xml(self, filepath):
        """Load dictionary from XML."""

        self.dictionary = dict()
        self.entity_types = list()
        dictionary_entry = {}

        with open(filepath, 'r') as xml_document:
            for line in xml_document:
                line = line.decode('utf8')

                # Entity ID.
                entity_id_match = re.match(r'.*<entity id="(?P<entity_id>\d+)">', line)
                if entity_id_match:
                    dictionary_entry['entity_id'] = entity_id_match.group('entity_id')

                # Entity Type.
                entity_type_match = re.match(r'.*<type>(?P<entity_type>.*)</type>', line)
                if entity_type_match:
                    entity_type = entity_type_match.group('entity_type')
                    entity_type = unidecode(entity_type)
                    entity_type = re.sub(r' ', '_', entity_type)
                    dictionary_entry['entity_type'] = entity_type

                # Entity Form.
                entity_form_match = re.match(r'.*<original_form>(?P<original_form>.*)</original_form>', line)
                if entity_form_match:
                    dictionary_entry['entity_form'] = entity_form_match.group('original_form').encode('utf8')

                # Lemmatized Form.
                lemmatized_form_match = re.match(r'.*<lemmatized>(?P<lemmatized>.*)</lemmatized>', line)
                if lemmatized_form_match:
                    dictionary_entry['lemmatized_form'] = lemmatized_form_match.group('lemmatized').encode('utf8')

                # Dependency tree nodes.
                node_match = re.match(r'.*<word form="(?P<form>.*)" lemma="(?P<lemma>.*)" tag="(?P<tag>.*)" ord="(?P<ord>.*)" parent="(?P<parent>.*)"/>', line)
                if node_match:
                    if 'dependency_tree' not in dictionary_entry:
                        dictionary_entry['dependency_tree'] = list()

                    node = {
                        'form': node_match.group('form').encode('utf8'),
                        'lemma': node_match.group('lemma').encode('utf8'),
                        'tag': node_match.group('tag'),
                        'order': int(node_match.group('ord')),
                        'parent': int(node_match.group('parent'))
                    }
                    dictionary_entry['dependency_tree'].append(node)

                # PML-TQ.
                pml_start_match = re.match(r'.*<pml_tq>(?P<pml_tq>.*)', line)
                if pml_start_match:
                    dictionary_entry['pml_tq'] = pml_start_match.group('pml_tq').encode('utf8')

                pml_end_match = re.match(r'(?P<pml_tq>.*)</pml_tq>', line)
                if pml_end_match:
                    dictionary_entry['pml_tq'] += '\n' + pml_end_match.group('pml_tq').encode('utf8')

                # Entity definition is done.
                entity_end_match = re.match(r'.*</entity>', line)
                if entity_end_match:
                    self.dictionary[dictionary_entry['entity_id']] = dictionary_entry
                    if dictionary_entry['entity_type'] not in self.entity_types:  # This is OK, there is no more than 30 different entity types.
                        self.entity_types.append(dictionary_entry['entity_type'])

                    dictionary_entry = dict()

        logging.info('Number of loaded entities: %d', len(self.dictionary))

    def load_json(self, filepath):
        """Load dictionary from JSON."""

        with open(filepath, 'r') as dictionary_json:
            data = json.load(dictionary_json)
            self.dictionary = data['entries']
            self.entity_types = data['entity_types']

        logging.info('Number of loaded entities: %d', len(self.dictionary))

    def save_json(self, filepath):
        """Load dictionary from XML."""

        data = {
            'entity_types': self.entity_types,
            'entries': self.dictionary
        }

        with open(filepath, 'w') as dictionary_json:
            json.dump(data, dictionary_json, ensure_ascii=False)
