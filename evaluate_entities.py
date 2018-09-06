#!/usr/bin/env python
#
# Author: (c) 2018 Vincent Kriz <kriz@ufal.mff.cuni.cz>
#

import re
import sys
import os
import json
import logging
import argparse


# Logging.
logging.basicConfig(format='%(asctime)-15s [%(levelname)7s] %(funcName)s - %(message)s', level=logging.DEBUG)


# Command line arguments.
parser = argparse.ArgumentParser()
parser.description = 'Entities detection evaluation.'
parser.add_argument('--elayer', required=True, help='directory with the goldstandard data')
parser.add_argument('--detected', required=True, help='rextractor entities output to evaluate')
args = parser.parse_args()


# Methods.
def load_detected_entities(file_path):
    detected_entities = []
    with open(file_path) as detected_entities_fh:
        for raw_description in detected_entities_fh:
            raw_description = raw_description.rstrip()
            fields = raw_description.split('\t')

            detected_entity = {
                'dictionary_id': "%04d" % int(fields[0]),
                'node_ids': [node_id[2:] for node_id in fields[1:]]
            }

            detected_entities.append(detected_entity)

    return detected_entities


def filter_overlapping_entities(entities):
    filtered_entities = []

    for candidate_entity in sorted(entities, key=lambda entity: len(entity['node_ids']), reverse=True):
        candidate_entity_nodes = set(candidate_entity['node_ids'])

        exists_more_specific_entity = False
        for filtered_entity in filtered_entities:
            filtered_entities_nodes = set(filtered_entity['node_ids'])
            if candidate_entity_nodes.issubset(filtered_entities_nodes):
                exists_more_specific_entity = True
                break

        if not exists_more_specific_entity:
            filtered_entities.append(candidate_entity)

    logging.info('Number of entities after overlapping filtering: %d', len(filtered_entities))
    return filtered_entities


def filter_fragmented_entities(entities):
    """Filter out entities such that their tokens are not in a one token sequence."""

    filtered_entities = []
    for candidate_entity in entities:
        continuous_entity = True

        previous_ord = None
        for node in sorted(candidate_entity['node_ids'], key=lambda node_id:int(re.sub(r'.*-node(\d+)', '\\1', node_id))):
            current_ord = int(re.sub(r'^.*node(\d+)$', r'\1', node))
            if previous_ord and current_ord != previous_ord + 1:
                continuous_entity = False
                break
            else:
                previous_ord = current_ord

        if continuous_entity:
            filtered_entities.append(candidate_entity)

    logging.info('Number of entities after continuous control: %d', len(filtered_entities))
    return filtered_entities



# Main.
if __name__ == "__main__":
    gs_files = sorted(os.listdir(args.elayer))

    n_total = 0
    n_tp = 0
    n_fp = 0
    n_fn = 0

    for file_name in gs_files:
        logging.info('')
        logging.info('*** %s ***', file_name)

        gs_entities_filename = "{}/{}".format(args.elayer, file_name)
        gs_entities = json.load(open(gs_entities_filename, 'r'))

        dt_entities_filename = "{}/{}.treex.gz.csv".format(args.detected, file_name[:-5])
        dt_entities = load_detected_entities(dt_entities_filename)

        dt_entities = filter_overlapping_entities(dt_entities)
        dt_entities = filter_fragmented_entities(dt_entities)

        n_total += len(gs_entities)

        matched_gold_entities = dict()
        for detected_entity in dt_entities:
            match_gs_entity = None
            logging.info('')
            logging.info('Looking for entity %s / %s', detected_entity['dictionary_id'], detected_entity['node_ids'])

            for gold_entity in gs_entities:
                if sorted(detected_entity['node_ids']) != sorted(gold_entity['node_ids']):
                    continue

                match_gs_entity = gold_entity
                matched_gold_entities['+'.join(sorted(match_gs_entity['node_ids']))] = 1

            if match_gs_entity:
                logging.info('TP')
                logging.info(' - GS = %s / %s', match_gs_entity['dictionary_id'], ', '.join(sorted(match_gs_entity['node_ids'])))
                logging.info(' - DT = %s / %s', detected_entity['dictionary_id'], ', '.join(sorted(detected_entity['node_ids'])))
                n_tp += 1

            else:
                logging.info('')
                logging.info('FP')
                logging.info(' - DT = %s / %s', detected_entity['dictionary_id'], ', '.join(sorted(detected_entity['node_ids'])))
                n_fp += 1

        for gold_entity in gs_entities:
            gold_hash = '+'.join(sorted(gold_entity['node_ids']))
            if gold_hash not in matched_gold_entities:
                logging.info('')
                logging.info('FN')
                logging.info(' - GH = %s', gold_hash)
                logging.info(' - GS = %s / %s', gold_entity['dictionary_id'], ', '.join(sorted(gold_entity['node_ids'])))
                n_fn += 1

    precision = n_tp / float(n_tp + n_fp)
    recall = n_tp / float(n_tp + n_fn)
    f1 = 2 * (precision * recall) / (precision + recall)

    logging.info('')
    logging.info('===================================')
    logging.info('Total = %6d', n_total)
    logging.info('TP    = %6d', n_tp)
    logging.info('FP    = %6d', n_fp)
    logging.info('FN    = %6d', n_fn)
    logging.info('Prec  = %f', precision)
    logging.info('Reca  = %f', recall)
    logging.info('===================================')
    logging.info('F1    = %f', f1)
