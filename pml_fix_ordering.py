#!/usr/bin/env python
#
# Author: (c) 2017 Vincent Kriz <kriz@ufal.mff.cuni.cz>
#

import re
import os
import logging
import argparse


# Logging.
logging.basicConfig(format='%(asctime)-15s [%(levelname)7s] %(funcName)s - %(message)s', level=logging.DEBUG)


# Command line arguments.
parser = argparse.ArgumentParser()
parser.description = 'Check and fix wrong ordering in the PML afiles.'
parser.add_argument('--input_dir', required=True, help='input directory')
parser.add_argument('--output_dir', required=True, help='output directory')
parser.add_argument('--triple_id', help='process only given triple id')
args = parser.parse_args()


def parse_id(a_node_id):
    """
    Parse A-node ID into particular attributes.

    """
    attributes = {}
    
    fields = a_node_id.split('-')
    for field in fields:
        document_match = re.match(r'document.*', field) 
        if document_match:
            attributes['document'] = field
        
        sentence_match = re.match(r'sentence(?P<sentence_id>\d+)', field)
        if sentence_match:
            attributes['sentence'] = int(sentence_match.group('sentence_id'))

        section_match = re.match(r'section(?P<section_id>\d+)', field)
        if section_match:
            attributes['section'] = int(section_match.group('section_id'))

        subsection_match = re.match(r'subsection(?P<subsection_id>\d+)', field)
        if subsection_match:
            attributes['subsection'] = int(subsection_match.group('subsection_id'))

        node_match = re.match(r'node(?P<node_id>\d+)', field)
        if node_match:
            attributes['node'] = int(node_match.group('node_id'))

    return attributes


def load_ordering(a_filename):
    """
    Create a dict {node_id => ord}.

    """
    logging.debug('Loading ordering from %s', a_filename)
    ordering = dict()

    # Create full path to the source files.
    a_path = '/'.join([args.input_dir, a_filename])

    # Remember the last parsed node ID.
    current_node = None

    # Read A file and parse nodes and their ord.
    with open(a_path, 'r') as a_file:
        for line in a_file:
            a_node_match = re.match(r'^\s+<(LM|children) id="(?P<node_id>.*)">', line)
            if a_node_match:
                current_node = a_node_match.group('node_id')
                continue

            ord_match = re.match(r'^\s+<ord>(?P<ord>\d+)</ord>', line)
            if ord_match:
                ordering[current_node] = ord_match.group('ord')

    return ordering


def detect_sentences(ordering):
    """
    Aggregate nodes that belong to the one sentence into a list.

    """
    sentences = []
    previous_sentence_id = ''
    sentence = []
    for a_node_id in sorted(ordering):
        attributes = parse_id(a_node_id)

        if previous_sentence_id and previous_sentence_id != attributes['sentence']:
            sentences.append(sentence)
            sentence = []

        sentence.append(a_node_id)
        previous_sentence_id = attributes['sentence']

    sentences.append(sentence)
    return sentences


def fix_ordering(ordering):
    """
    Check and fix errors in the given ordering. Return a fixed ordering that should be applied on A-file.

    """
    fixed_ordering = {}
    n_should_fix = 0

    sentences = detect_sentences(ordering)
    for sentence in sentences:
        logging.debug('')

        correct_ordering = {}
        for a_node_id in sentence:
            a_node_attributes = parse_id(a_node_id)
            ordering_key = '%03d.%03d.%03d' % (a_node_attributes.get('section', 0), a_node_attributes.get('subsection', 0), a_node_attributes.get('node', 0))
            correct_ordering[ordering_key] = a_node_id

        for (correct_ord, ordering_key) in enumerate(sorted(correct_ordering)):
            a_node_id = correct_ordering[ordering_key]
            fixed_ordering[a_node_id] = correct_ord

            should_fix = ' '
            if str(correct_ord) != ordering[a_node_id]:
                n_should_fix += 1
                should_fix = 'X'

            logging.debug('| %s | %3d | %3s | %20s |', should_fix, correct_ord, ordering[a_node_id], a_node_id)

    logging.info('Number of nodes to be fixed: %d', n_should_fix)
    return fixed_ordering


def update_afile(a_filename, correct_ordering):
    """
    Change ords tags according to the given correct ordering.

    """
    # Create full path to the source files.
    a_path_input = '/'.join([args.input_dir, a_filename])
    a_path_output = '/'.join([args.output_dir, a_filename])

    # Read W file and change identifiers according to mapping
    with open(a_path_input, 'r') as a_file_input:
        with open(a_path_output, 'w') as a_file_output:
            current_a_node_id = ''
            for line in a_file_input:
                a_node_match = re.match(r'\s*<(LM|children) id="(?P<node_id>.*)">', line)
                ord_match = re.match(r'\s*<ord>(?P<ord>\d+)</ord>', line)

                if a_node_match:
                    current_a_node_id = a_node_match.group('node_id')
                    if current_a_node_id not in correct_ordering:
                        logging.error('Missing A-node ID %s', current_a_node_id)

                if ord_match:
                    original_ord = int(ord_match.group('ord'))
                    fixed_ord = correct_ordering[current_a_node_id]
                    if original_ord != fixed_ord:
                        logging.info('Updating %s from %d to %d', current_a_node_id, original_ord, fixed_ord)
                        line = re.sub(r'<ord>.*</ord>', '<ord>%s</ord>' % fixed_ord, line)

                a_file_output.write(line)


# Main.
if __name__ == "__main__":
    files = sorted(os.listdir(args.input_dir))

    while len(files) >= 3:
        pml_a, pml_m, pml_w = files.pop(0), files.pop(0), files.pop(0)

        if pml_a[-1] != 'a':
            continue
        if pml_m[-1] != 'm':
            continue
        if pml_w[-1] != 'w':
            continue

        triple_id = pml_a[:-2]
        if args.triple_id:
            if triple_id != args.triple_id:
                logging.info('Skipping triple ID %s', triple_id)
                continue

        logging.info('')
        logging.info('*** %s ***', pml_a)
        logging.info('')

        # Load original files and analyze used identifiers.
        current_ordering = load_ordering(pml_a)
        fixed_ordering = fix_ordering(current_ordering)
        # update_afile(pml_a, fixed_ordering)
