# Czech Legal Text Treebank Tools

This repository contains several tools that were used for preparing the CLTT 2.0 version.

## New PML Identifiers

`pml_update_identifiers.py`

Identifiers in the PML files in CLTT 1.0 were not consistent and there were no exact
rules how they should be defined. In CLTT 2.0 we will update all identifiers to fulfill exact 
and simple naming conventions. 

## Fixing wrong word order

`pml_fix_ordering.py`

Several sentences in CLTT 1.0 had wrong word ordering as a result of some bug during
merging complex sentences from segments. This tool checks and fixes word ordering 
in the whole CLTT 2.0.
