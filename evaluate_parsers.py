#!/usr/bin/env python
#
# Author: (c) 2017 Vincent Kriz <kriz@ufal.mff.cuni.cz>
#

import os
import logging
import argparse


# Logging.
logging.basicConfig(format='%(asctime)-15s [%(levelname)7s] %(funcName)s - %(message)s', level=logging.DEBUG)


# Command line arguments.
parser = argparse.ArgumentParser()
parser.description = 'Calculate the Unlabeled Attachment Score for given PRS files.'
parser.add_argument('--goldstandard_dir', required=True, help='directory with the goldstandard data')
parser.add_argument('--evaluation_dir', required=True, help='parser output to evaluate')
parser.add_argument('--segments_dir', required=False, help='segments mapping to sentences')
args = parser.parse_args()


# Constants.
TOKENS_SEPARATOR = '#'
FIELDS_SEPARATOR = '|'


# Methods.
def load_sentences(file_path, segments=None):
    """
    Load the sentences from the given file.

    """
    # Load all sentences (or segments).
    sentences = []
    with open(file_path, 'r') as document:
        for line in document:
            sentence = parse_sentence(line)
            sentences.append(sentence)

    # If segments are specifies, sentences list contains segments.
    # Use segments definition to join defined number of segments into sentences.
    if not segments:
        return sentences

    logging.info('')
    logging.info('--> segments joining -->')

    sentences.reverse()
    segments.reverse()
    joined_sentences = []
    while segments:
        n_requested_segments = segments.pop()
        n_loaded_segments = 0
        sentence = []

        logging.info('SENTENCE REQUIRE : %d', n_requested_segments)
        while n_loaded_segments != n_requested_segments:
            segment = sentences.pop()

            # Remove the root from the second and next segments.
            if n_loaded_segments:
                segment = segment[1:]

            # Update segment's ords.
            segment = transform_ords(sentence, segment)

            # Join current segment to already joined segments.
            sentence.extend(segment)
            n_loaded_segments += 1

        joined_sentences.append(sentence)

    return joined_sentences


def transform_ords(joined_segments, current_segment):
    """
    When a new segment is joined to already joined segments, we must update its ords to be unique in the
    whole complex sentence.

    """
    # Find max ord in already joined segments.
    maximal_ord = 0
    for token in joined_segments:
        maximal_ord = max(maximal_ord, token['ord'])

    # Update ord attributes.
    for token in current_segment:
        token['ord'] += maximal_ord
        if token['parent'] > 0:
            token['parent'] += maximal_ord

    return current_segment


def parse_sentence(raw_line):
    """
    Return the sentence structure encoded in the given string.

    """
    raw_line = raw_line.decode('utf-8')
    raw_line = raw_line.rstrip()

    root_token = {
        'form': '_',
        'ord': 0,
        'parent': 0,
        'a_ord': None,
        'a_form': None,
        'a_parent': None,
        'gs_parent': None
    }

    sentence = list()
    sentence.append(root_token)

    raw_tokens = raw_line.split(TOKENS_SEPARATOR)
    for raw_token in raw_tokens:
        try:
            data_fields = raw_token.split(FIELDS_SEPARATOR)
            token = {
                'ord': int(data_fields[0]),
                'form': data_fields[1],
                'parent': int(data_fields[2]),
                'a_ord': None,
                'a_form': None,
                'a_parent': None,
                'gs_parent': None
            }
            sentence.append(token)
        except Exception:
            logging.error('Invalid token %r', raw_token)
            logging.error('Parsing error for line %r', raw_line)

    return sentence


def print_sentence(sentence):
    """
    Pretty sentence printing.

    """
    # Header.
    logging.debug('')
    logging.debug('    +-%4s-+-%4s-+-%20s-++-%4s-+-%4s-+-%20s-++-%4s-+-%1s-+', '-' * 4, '-' * 4, '-' * 20, '-' * 4, '-' * 4, '-' * 20, '-' * 4, '-' * 1)
    logging.debug('    | %4s | %4s | %20s || %4s | %4s | %20s || %4s | %1s |', 'E O', 'E P', 'E F', 'A O', 'A P', 'A F', 'GS', 'M')
    logging.debug('    +-%4s-+-%4s-+-%20s-++-%4s-+-%4s-+-%20s-++-%4s-+-%1s-+', '-' * 4, '-' * 4, '-' * 20, '-' * 4, '-' * 4, '-' * 20, '-' * 4, '-' * 1)

    # Tokens.
    for token in sentence:
        match = ' '
        if token['a_ord'] > 0 and token['a_parent'] == token['gs_parent']:
            match = 'x'

        logging.debug('    | %4s | %4s | %20s || %4s | %4s | %20s || %4s | %s |',
                      token['ord'], token['parent'], token['form'],
                      token['a_ord'], token['a_parent'], token['a_form'],
                      token['gs_parent'], match)

    # Footer.
    logging.debug('    +-%4s-+-%4s-+-%20s-++-%4s-+-%4s-+-%20s-++-%4s-+-%1s-+', '-' * 4, '-' * 4, '-' * 20, '-' * 4, '-' * 4, '-' * 20, '-' * 4, '-' * 1)


def get_gs_ev_alignment(evaluated_sentence, goldstandard_sentence):
    """
    Obtain the alignment between the sentences.

    """
    ev2gs_mapping = {}
    gs_index = 0
    ev_index = 0

    while gs_index < len(goldstandard_sentence):
        try:
            ev_token = evaluated_sentence[ev_index]
            gs_token = goldstandard_sentence[gs_index]
        except IndexError:
            logging.error('Index problem')
            break

        logging.debug('Aligning GS token %s', goldstandard_sentence[gs_index]['form'])

        if gs_token['form'] == ev_token['form']:
            ev_token['a_ord'] = gs_token['ord']
            ev2gs_mapping[ev_token['ord']] = ev_token['a_ord']
            ev_token['a_form'] = gs_token['form']
            ev_token['gs_parent'] = gs_token['parent']
            gs_index += 1
            ev_index += 1
        else:
            # Try next ev tokens to match the current GS node.
            found_ev_token = False
            local_ev_index = ev_index + 1
            while local_ev_index < len(evaluated_sentence):
                if evaluated_sentence[local_ev_index]['form'] == goldstandard_sentence[gs_index]['form']:
                    logging.debug(' --> GS token found in the EV sentence : %d/%s', local_ev_index, evaluated_sentence[local_ev_index]['form'])
                    ev_index = local_ev_index
                    found_ev_token = True
                    break

                local_ev_index += 1

            if found_ev_token:
                continue

            # Otherwise, let's to the next GS token
            gs_index += 1

            # while evaluated_sentence[ev_index]['form'] != goldstandard_sentence[gs_index]['form']:
            #     gs_index += 1
            #     local_ev_index = ev_index
            #
            #     if local_ev_index >= len(evaluated_sentence):
            #         continue
            #
            #     if gs_index >= len(goldstandard_sentence):
            #         break
            #
            #     while evaluated_sentence[local_ev_index]['form'] != goldstandard_sentence[gs_index]['form']:
            #         local_ev_index += 1
            #
            #         if local_ev_index >= len(evaluated_sentence):
            #             break

    # Set alignment parents according to the ev2gs_mapping.
    for ev_token in evaluated_sentence:
        if ev_token['parent'] in ev2gs_mapping:
            ev_token['a_parent'] = ev2gs_mapping[ev_token['parent']]


def compare_sentences(gs_sentence, ev_sentence):
    """
    Return the number of tokens with the corrent parent and the total number of tokens to be evaluated.

    """
    get_gs_ev_alignment(ev_sentence, gs_sentence)
    print_sentence(ev_sentence)

    correct_tokens = 0
    total_tokens = 0
    for token in ev_sentence[1:]:
        if not token['a_parent']:
            continue

        total_tokens += 1
        if token['a_parent'] == token['gs_parent']:
            correct_tokens += 1

    return correct_tokens, total_tokens


def load_segments(file_path):
    """
    Load segments description to determine which segment belong to which GS sentence

    """
    if not file_path:
        return None

    segments_counts = []
    with open(file_path) as segments_description:
        for raw_description in segments_description:
            raw_description = raw_description.rstrip()
            n_segments = int(raw_description)
            segments_counts.append(n_segments)

    return segments_counts


# Main.
if __name__ == "__main__":
    gs_files = sorted(os.listdir(args.goldstandard_dir))

    tokens_ev = 0
    tokens_gs = 0

    tokens_correct = 0
    tokens_total = 0

    for file_name in gs_files:
        logging.info('')
        logging.info('*** %s ***', file_name)

        segments_file_path = None
        if args.segments_dir:
            segments_file_path = '/'.join([args.segments_dir, file_name[:-3] + 'sgs'])
        gs_file_path = '/'.join([args.goldstandard_dir, file_name])
        ev_file_path = '/'.join([args.evaluation_dir, file_name])

        segments_des = load_segments(segments_file_path)
        gs_sentences = load_sentences(gs_file_path)
        ev_sentences = load_sentences(ev_file_path, segments=segments_des)

        for (gs_sentence, ev_sentence) in zip(gs_sentences, ev_sentences):
            n_correct_tokens, n_total_tokens = compare_sentences(gs_sentence, ev_sentence)

            tokens_ev += len(ev_sentence) - 1
            tokens_gs += len(gs_sentence) - 1

            tokens_correct += n_correct_tokens
            tokens_total += n_total_tokens

            logging.debug('')
            logging.debug('-----------------------------')
            logging.debug('')

    logging.info('')
    logging.info('===================================')
    logging.info('Total tokens in evaluated data    = %6d', tokens_ev)
    logging.info('Total tokens in goldstandard data = %6d', tokens_gs)
    logging.info('Total alignment tokens            = %6d', tokens_total)
    logging.info('Total correct tokens              = %6d', tokens_correct)
    logging.info('===================================')
    logging.info('UAS                               = %f', tokens_correct / float(tokens_total))
