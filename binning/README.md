####The procedure is as follows:

1. tax-rankify: Convert taxonomic IDs to class identifiers at specified taxonomic levels.
2. confusion-matrix: Convert label and prediction file into a confusion matrix.
3. cmat2XXX: do things with the confusion matrices.

Example:

##### prepare files
```bash
tax-rankify -t taxonomy.sqlite < data.labels.tax > data.labels.racol
tax-rankify -t taxonomy.sqlite < data.predictions.tax > data.predictions.racol
fasta-seqlen < data.fna > data.seqlen
```

##### geneate matrix
```bash
confusion-matrix --rows data.labels.racol --columns data.predictions.racol --weights data.seqlen --matrix-form quadratic --allow-missing-columns > data.cmat
```

##### display statistics for each matrix
```bash
cmat2stat < data.cmat
```

If you are comparing non-taxonomic binning classes, step a can be skipped.
Questions: johannes.droege@uni-duesseldorf.de
