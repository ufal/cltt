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
import xmltodict


# Logging.
logging.basicConfig(format='%(asctime)-15s [%(levelname)7s] %(funcName)s - %(message)s', level=logging.DEBUG)


# Command line arguments.
parser = argparse.ArgumentParser()
parser.description = 'Take DBE in XML format and create a Treex scenario for Rextractor.'
parser.add_argument('--dbe', required=True, help='DBE XML')
parser.add_argument('--scenario', required=True, help='output treex scenario')
args = parser.parse_args()


# Methods.
def load_dbe(filepath):
    dbe = list()
    raw_dbe = xmltodict.parse(open(filepath, 'r'))
    for raw_dbe_entry in raw_dbe['entities']['entity']:
        entity_id = raw_dbe_entry['@id']
        pml_tq = raw_dbe_entry['pml_tq']
        logging.info('DBE Entry #%s = %s', entity_id, pml_tq)

        dbe.append({'id': entity_id, 'tq': pml_tq})
    return dbe


# Main.
if __name__ == "__main__":
    dbe = load_dbe(args.dbe)
    queries = list()
    action_template = 'print "{0}\\t"; foreach my $node (@nodes) {{ $node->{{wild}}{{intlib}}{{{0}}} = 1; $node->serialize_wild(); print $node->{{id}} . "\\t"}}; print "\\n"'

    for dbe_entry in dbe:
        query = dbe_entry['tq']
        query = re.sub(r"\n\s*>>.*$", "", query)
        query = re.sub(r"m/lemma", "lemma", query)

        dbe_id = dbe_entry['id']
        dbe_id = re.sub(r"^0+", "", dbe_id)

        action = '%s' % action_template
        action = action.format(dbe_id)
        queries.append("Util::PMLTQ query='%s' action='%s'" % (query, action))

    with open(args.scenario, 'w') as output_fh:
        for query in queries:
            output_fh.write(query.encode('utf-8'))
            output_fh.write('\n')
