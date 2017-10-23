#!/usr/bin/env python
#
# Author: (c) 2017 Vincent Kriz <kriz@ufal.mff.cuni.cz>
#

import os
import logging
import argparse

from cltt.accounting_dictionary import Dictionary


# Logging.
logging.basicConfig(format='%(asctime)-15s [%(levelname)7s] %(funcName)s - %(message)s', level=logging.DEBUG)


# Command line arguments.
parser = argparse.ArgumentParser()
parser.description = 'Build JSON Accouting Dictionary from XML.'
parser.add_argument('--xml', required=True, help='Accounting Dictionary (JSON file)')
parser.add_argument('--json', required=True, help='Efind output directory')
args = parser.parse_args()


if __name__ == "__main__":
    # Accounting Dictionary.
    accounting_dictionary = Dictionary()
    accounting_dictionary.load_xml(args.xml)
    accounting_dictionary.save_json(args.json)
