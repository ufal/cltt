#!/usr/bin/env python
#
# Author: (c) 2017 Vincent Kriz <kriz@ufal.mff.cuni.cz>
#

import re
import logging
import argparse

# Logging.
logging.basicConfig(format='%(asctime)-15s [%(levelname)7s] %(funcName)s - %(message)s', level=logging.INFO)


# Command line arguments.
parser = argparse.ArgumentParser()
parser.description = 'Reorder dictionary entries.'
parser.add_argument('--dictionary', required=True, help='Accounting Dictionary (XML file)')
parser.add_argument('--output', required=True, help='Updated XML file')
args = parser.parse_args()


if __name__ == "__main__":
    entries_counter = 0
    with open(args.output, 'w') as output_dictionary:
        with open(args.dictionary, 'r') as input_dictionary:
            for line in input_dictionary:
                entry_match = re.match(r'^\s+<entity id="\d+">$', line)
                if entry_match:
                    entries_counter += 1
                    output_dictionary.write('	<entity id="%04d">\n' % entries_counter)
                else:
                    output_dictionary.write(line)
