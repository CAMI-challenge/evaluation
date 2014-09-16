The procedure is as follows:

a) tax-rankify: Convert taxonomic IDs to class identifiers at specified taxonomic levels
b) confusion-matrix: Convert label and prediction file into a confusion matrix
c) cmat2XXX: do things with the confusion matrices

Example:

# prepare files
tax-rankify -t taxonomy.sqlite < data.labels.tax > data.labels.racol
tax-rankify -t taxonomy.sqlite < data.predictions.tax > data.predictions.racol
fasta-seqlen < data.fna > data.seqlen

# geneate matrix
confusion-matrix --rows data.labels.racol --columns data.predictions.racol --weights data.seqlen --matrix-form quadratic --allow-missing-columns > data.cmat

# display statistics for each matrix
cmat2stat < data.cmat

If you are comparing non-taxonomic binning classes, step a can be skipped.
Questions: johannes.droege@uni-duesseldorf.de
