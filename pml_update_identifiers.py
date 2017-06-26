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
parser.description = 'Consolidate the IDs in the PML files.'
parser.add_argument('--input_dir', required=True, help='input directory')
parser.add_argument('--output_dir', required=True, help='output directory')
parser.add_argument('--triple_id', help='process only given triple id')
args = parser.parse_args()


# Methods.
def analyze_mfile(m_filename):
    """
    Load the M-file, parse sentence tags <s ...> and create a new sentence identifiers.

    """
    sentence_mapping = list()
    sentence_counter = 0
    section_counter = 0
    subsection_counter = 0

    # Create full path to the source files.
    m_path = '/'.join([args.input_dir, m_filename])

    # Obtain the document ID.
    document_id = m_filename[:-2]
    local_sentence_counter = 0
    logging.info('Document ID: %s', document_id)

    # Remember previous m-node.
    previous_m_node = None
    m2w_mapping = {}

    # Read M file and parse sentence IDs.
    with open(m_path, 'r') as m_file:
        for line in m_file:
            line = re.sub(r'^\s+', '', line)

            # Match important things.
            m_node_match = re.match(r'.*<m id=".*-(?P<m_node_id>p.*-Tm)">', line)
            w_node_match = re.match(r'.*<w.rf>w#(?P<w_node_id>.*)</w.rf', line)
            sentence = re.match(r'<s id=".*-p(?P<paragraph>\d+)s(?P<sentence>.*?)">', line)

            # Create the w2m nodes mapping.
            if m_node_match:
                previous_m_node = m_node_match.group('m_node_id')
                continue

            if w_node_match:
                m2w_mapping[previous_m_node] = w_node_match.group('w_node_id')
                continue

            if not sentence:
                continue

            paragraph_id = sentence.group('paragraph')
            sentence_id = sentence.group('sentence')

            # Simple sentences.
            if re.match(r'^\d+$', sentence_id):
                sentence_counter += 1
                section_counter = 0
                subsection_counter = 0
                local_sentence_counter += 1

                sentence_mapping.append({
                    'has_section': False,
                    'has_subsection': False,
                    'document_id': document_id,
                    'local_id': local_sentence_counter,
                    'paragraph_id': paragraph_id,
                    'sentence_id': sentence_id,
                    'new_a_sentence_id': '%s-sentence%d' % (document_id, sentence_counter),
                    'new_m_sentence_id': '%s-sentence%d' % (document_id, sentence_counter)
                })
                continue

            # Complex sentences with sections.
            if re.match(r'^\d+-\d+$', sentence_id):
                if not sentence_mapping[-1]['has_section']:
                    section_counter = 0
                    sentence_mapping[-1]['new_m_sentence_id'] = '%s-sentence%d-section%d' % (document_id, sentence_counter, section_counter)

                section_counter += 1
                subsection_counter = 0

                sentence_mapping.append({
                    'has_section': True,
                    'has_subsection': False,
                    'document_id': document_id,
                    'local_id': local_sentence_counter,
                    'paragraph_id': paragraph_id,
                    'sentence_id': sentence_id,
                    'new_a_sentence_id': '%s-sentence%d' % (document_id, sentence_counter),
                    'new_m_sentence_id': '%s-sentence%d-section%d' % (document_id, sentence_counter, section_counter)
                })
                continue

            # Complex sentences with subsections.
            if re.match(r'^\d+-\d+-\d+$', sentence_id):
                if not sentence_mapping[-1]['has_subsection']:
                    subsection_counter = 0
                    sentence_mapping[-1]['new_m_sentence_id'] = '%s-sentence%d-section%d-subsection%d' % (document_id, sentence_counter, section_counter, subsection_counter)

                subsection_counter += 1

                sentence_mapping.append({
                    'has_section': True,
                    'has_subsection': True,
                    'document_id': document_id,
                    'local_id': local_sentence_counter,
                    'paragraph_id': paragraph_id,
                    'sentence_id': sentence_id,
                    'new_a_sentence_id': '%s-sentence%d' % (document_id, sentence_counter),
                    'new_m_sentence_id': '%s-sentence%d-section%d-subsection%d' % (document_id, sentence_counter, section_counter, subsection_counter)
                })
                continue

    for sentence in sentence_mapping:
        logging.info('%4d | %20s | %5s | %10s | %30s | %40s', sentence['local_id'], sentence['document_id'], sentence['paragraph_id'],
                     sentence['sentence_id'], sentence['new_a_sentence_id'], sentence['new_m_sentence_id'])

    final_mapping = dict()
    for mapping_rule in sentence_mapping:
        old_id = 'p%ss%s' % (mapping_rule['paragraph_id'], mapping_rule['sentence_id'])
        final_mapping[old_id] = mapping_rule['new_m_sentence_id']

    return final_mapping, m2w_mapping


def analyze_afile(a_filename, m_sentence_mapping, m_node2w_node_mapping):
    """
    Load the A-file, parse a-nodes <m ...> tags.

    """
    a_sentences = list()

    # Create full path to the source files.
    a_path = '/'.join([args.input_dir, a_filename])

    # Obtain the document ID.
    document_id = a_filename[:-2]
    logging.info('Document ID: %s', document_id)

    # Remember the last parsed sentence ID.
    current_sentence = None

    # Read M file and parse sentence IDs.
    with open(a_path, 'r') as a_file:
        for line in a_file:
            a_sentence = re.match(r'\s{4}<LM id=".*-(?P<sentence_id>p(?P<paragraph>\d+)s(?P<sentence>.*?))">', line)
            if a_sentence:
                if current_sentence:
                    a_sentences.append(current_sentence)

                current_sentence = {'a_sentence_id': a_sentence.group('sentence_id'), 'm_sentence_id': '', 'a_nodes': [], 'm_nodes': []}
                continue

            m_sentence = re.match(r'\s+<s.rf>.*-(?P<sentence_id>p(?P<paragraph>\d+)s(?P<sentence>.*?))</s.rf>', line)
            if m_sentence:
                current_sentence['m_sentence_id'] = m_sentence.group('sentence_id')
                continue

            a_node = re.match(r'^\s+<(LM|children) id=".*-(?P<node_id>p(?P<paragraph>\d+)s(?P<sentence>.*?)W(?P<node>\d+)-Tm)">', line)
            if a_node:
                current_sentence['a_nodes'].append(a_node.group('node_id'))
                continue

            m_node = re.match(r'^\s+<m.rf>.*-(?P<node_id>p(?P<paragraph>\d+)s(?P<sentence>.*?)W(?P<node>\d+)-Tm)</m.rf>', line)
            if m_node:
                current_sentence['m_nodes'].append(m_node.group('node_id'))

        if current_sentence:
            a_sentences.append(current_sentence)

    # Prepare final mappings.
    final_a_nodes_mapping = dict()
    final_m_nodes_mapping = dict()
    final_w_nodes_mapping = dict()

    for sentence in a_sentences:
        logging.info('')
        logging.info('*** %s (%s) --> %s ***', sentence['a_sentence_id'], sentence['m_sentence_id'], m_sentence_mapping[sentence['m_sentence_id']])
        logging.info('')

        for i in range(len(sentence['a_nodes'])):
            original_a_node_id = sentence['a_nodes'][i]
            original_m_node_id = sentence['m_nodes'][i]
            original_w_node_id = m_node2w_node_mapping[original_m_node_id]

            match = ''
            if original_a_node_id != original_m_node_id:
                match = 'x'

            a_node_id_extraction = re.match('.*(?P<original_a_sentence_id>p.*)W(?P<a_w_value>\d+).*', original_a_node_id)
            original_a_sentence_id = a_node_id_extraction.group('original_a_sentence_id')
            a_w_value = a_node_id_extraction.group('a_w_value')
            new_sentence_id = sentences_mapping[original_a_sentence_id]
            final_a_nodes_mapping[original_a_node_id] = '%s-node%s' % (new_sentence_id, a_w_value)

            m_node_id_extraction = re.match('.*(?P<original_m_sentence_id>p.*)W(?P<m_w_value>\d+).*', original_m_node_id)
            original_m_sentence_id = m_node_id_extraction.group('original_m_sentence_id')
            m_w_value = m_node_id_extraction.group('m_w_value')
            new_sentence_id = sentences_mapping[original_m_sentence_id]
            final_m_nodes_mapping[original_m_node_id] = '%s-node%s' % (new_sentence_id, m_w_value)
            final_w_nodes_mapping[original_w_node_id] = '%s-node%s' % (new_sentence_id, m_w_value)

            logging.info('    | %20s | %45s || %1s || %20s | %45s |', original_m_node_id, final_m_nodes_mapping[original_m_node_id], match, original_a_node_id, final_a_nodes_mapping[original_a_node_id])

    return final_a_nodes_mapping, final_m_nodes_mapping, final_w_nodes_mapping


def update_afile_identifiers(a_filename, sentence_id_mapping, a_nodes_mapping, m_nodes_mapping):
    """
    Load the A-file, change the sentence identifiers, change the nodes identifiers and return them as a mapping.

    """
    # Create full path to the source files.
    a_path_input = '/'.join([args.input_dir, a_filename])
    a_path_output = '/'.join([args.output_dir, a_filename])

    # Read W file and change identifiers according to mapping
    with open(a_path_input, 'r') as a_file_input:
        with open(a_path_output, 'w') as a_file_output:
            for line in a_file_input:
                a_node = re.match(r'\s*<(LM|children) id=".*-(?P<old_node_id>p.*-Tm)">', line)
                m_node_reference = re.match(r'\s*<m.rf>.*-(?P<old_node_id>p.*-Tm)</m.rf>', line)
                m_sentence_reference = re.match(r'\s*<s.rf>.*-(?P<old_sentence_id>p.*)</s.rf>', line)
                a_sentence = re.match(r'^\s{4}<LM id=".*-(?P<old_sentence_id>p.*?)">', line)

                if a_sentence:
                    original_sentence_id = a_sentence.group('old_sentence_id')
                    if original_sentence_id not in sentence_id_mapping:
                        logging.warning('Unknown sentence ID %s on line : %r', original_sentence_id, line)
                        continue

                    new_sentence_id = sentence_id_mapping[original_sentence_id]

                    # Remove section/subsection from the A sentence ID.
                    new_sentence_id = re.sub(r'-section\d+', '', new_sentence_id)
                    new_sentence_id = re.sub(r'-subsection\d+', '', new_sentence_id)

                    line = re.sub(r'id=".*"', 'id="a-%s"' % new_sentence_id, line)

                elif m_sentence_reference:
                    original_sentence_id = m_sentence_reference.group('old_sentence_id')
                    if original_sentence_id not in sentence_id_mapping:
                        logging.warning('Unknown sentence ID %s on line : %r', original_sentence_id, line)
                        continue

                    new_sentence_id = sentence_id_mapping[original_sentence_id]
                    line = re.sub(r'<s.rf>.*</s.rf>', '<s.rf>m#m-%s</s.rf>' % new_sentence_id, line)

                elif a_node:
                    original_node_id = a_node.group('old_node_id')
                    if original_node_id not in a_nodes_mapping:
                        logging.warning('Unknown node ID %s on line : %r', original_node_id, line)
                        continue

                    new_node_id = a_nodes_mapping[original_node_id]
                    line = re.sub(r'id=".*"', 'id="a-%s"' % new_node_id, line)

                elif m_node_reference:
                    original_node_id = m_node_reference.group('old_node_id')
                    if original_node_id not in m_nodes_mapping:
                        logging.warning('Unknown node ID %s on line : %r', original_node_id, line)
                        continue

                    new_node_id = m_nodes_mapping[original_node_id]
                    line = re.sub(r'<m.rf>.*</m.rf>', '<m.rf>m#m-%s</m.rf>' % new_node_id, line)

                a_file_output.write(line)


def update_mfile_identifiers(m_filename, sentence_id_mapping, m_nodes_mapping, w_nodes_mapping):
    """
    Load the M-file, change the sentence identifiers, change the nodes identifiers and return them as a mapping.

    """
    # Create full path to the source files.
    m_path_input = '/'.join([args.input_dir, m_filename])
    m_path_output = '/'.join([args.output_dir, m_filename])

    # Read W file and change identifiers according to mapping
    with open(m_path_input, 'r') as m_file_input:
        with open(m_path_output, 'w') as m_file_output:
            for line in m_file_input:
                w_node_match = re.match(r'\s*<w.rf>w#(?P<original_node_id>.*)</w.rf>', line)
                m_node_match = re.match(r'\s*<m id=".*-(?P<original_node_id>p.*-Tm)">', line)
                sentence_match = re.match(r'\s*<s id=".*-(?P<old_sentence_id>p.*?)">', line)

                if w_node_match:
                    original_node_id = w_node_match.group('original_node_id')
                    if original_node_id not in w_nodes_mapping:
                        logging.warning('Unknown node ID %s on line : %r', original_node_id, line)
                        continue

                    new_node_id = w_nodes_mapping[original_node_id]
                    line = re.sub(r'<w.rf>.*</w.rf>', '<w.rf>w#w-%s</w.rf>' % new_node_id, line)

                if m_node_match:
                    original_node_id = m_node_match.group('original_node_id')
                    if original_node_id not in m_nodes_mapping:
                        logging.warning('Unknown node ID %s on line : %r', original_node_id, line)
                        continue

                    new_node_id = m_nodes_mapping[original_node_id]
                    line = re.sub(r'id=".*"', 'id="m-%s"' % new_node_id, line)

                if sentence_match:
                    original_sentence_id = sentence_match.group('old_sentence_id')
                    if original_sentence_id not in sentence_id_mapping:
                        logging.warning('Unknown sentence ID %s on line : %r', original_sentence_id, line)
                        continue

                    new_sentence_id = sentence_id_mapping[original_sentence_id]
                    line = re.sub(r'id=".*"', 'id="s-%s"' % new_sentence_id, line)

                m_file_output.write(line)


def update_wfile_identifiers(w_filename, w_nodes_mapping):
    """
    Load the W-file, remove <params> tags, change the nodes identifiers.

    """
    # Create full path to the source files.
    w_path_input = '/'.join([args.input_dir, w_filename])
    w_path_output = '/'.join([args.output_dir, w_filename])

    # Read W file and change identifiers according to mapping
    with open(w_path_input, 'r') as w_file_input:
        with open(w_path_output, 'w') as w_file_output:
            for line in w_file_input:
                lines_to_skip_match = re.match(r'\s*</?(para|othermarkup).*', line)
                node_match = re.match(r'\s*<w id="(?P<original_node_id>.*)">', line)

                if lines_to_skip_match:
                    continue

                if node_match:
                    original_node_id = node_match.group('original_node_id')
                    if original_node_id not in w_nodes_mapping:
                        logging.warning('Unknown node ID %s on line : %r', original_node_id, line)
                        continue

                    new_node_id = w_nodes_mapping[original_node_id]
                    line = re.sub(r'id=".*"', 'id="w-%s"' % new_node_id, line)

                w_file_output.write(line)


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

        # Load original files and analyze used identifiers.
        sentences_mapping, wnodes_mapping = analyze_mfile(pml_m)
        anodes_mapping, mnodes_mapping, wnodes_mapping = analyze_afile(pml_a, sentences_mapping, wnodes_mapping)

        # Create new files with updated identifiers.
        update_wfile_identifiers(pml_w, wnodes_mapping)
        update_mfile_identifiers(pml_m, sentences_mapping, mnodes_mapping, wnodes_mapping)
        update_afile_identifiers(pml_a, sentences_mapping, anodes_mapping, mnodes_mapping)
