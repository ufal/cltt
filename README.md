# Czech Legal Text Treebank Tools and Data

[Czech Legal Text Treebank](https://ufal.mff.cuni.cz/czech-legal-text-treebank)

This repository contains several tools that were used for preparing the CLTT 2.0 version.
It also contains the PML part of the data (only [wma] layers) so that annotation errors
found after the CLTT 2.0 release can be fixed somewhere.

## Tools

### New PML Identifiers

`pml_update_identifiers.py`

Identifiers in the PML files in CLTT 1.0 were not consistent and there were no exact
rules how they should be defined. In CLTT 2.0 we will update all identifiers to fulfill exact 
and simple naming conventions. 

### Fixing wrong word order

`pml_fix_ordering.py`

Several sentences in CLTT 1.0 had wrong word ordering as a result of some bug during
merging complex sentences from segments. This tool checks and fixes word ordering 
in the whole CLTT 2.0.

## Data

The folder `data/sentences/pml` corresponds to `sentences/pml` in the [CLTT 2.0 release
package](http://hdl.handle.net/11234/1-2498) (see also `/net/data/treebanks/cs/cltt-2.0/sentences/pml`).

