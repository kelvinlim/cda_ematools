# cda_ematools

Tools for applying causal discovery analysis to ecological momentary analysis data.

## Key steps for basic analysis

1. Wrangle the data if needed. This may be needed to make it compatible with the next step.
2. Parse data and normalize it
3. Apply the causal discovery analysis to model a causal graph
4. Apply the SEM to compute strength and sign of edges in the causal graph
5. Create summary docx with the plots
6. Create fancier output
7. An example dataset is provided to illustrate how to use these tools.

## Wrangle data

This typically is done using some custom code to handle special cirumstances of the incoming data.

Examples of programs for dealing with different sources will be provided here.

## Parse data

Generally we expect the data to be in a csv file with columns containing the variables and rows the measurements for each subject. Mulitple subjects can be in a file, with an id column containing the subject identifier.

The parsedata.py program is designed to handle many different transformations of the data, to prepare it for next steps in processing.

Activity of the program is directed by a config.yaml file which directs the program what to do.  This allows customization of processing without having to write code.

Need a description of the config.yaml file.
