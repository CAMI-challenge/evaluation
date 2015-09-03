#!/bin/bash
#
#   evaluate-binning.bash - Generates statistics for binning results and writes
#                           them in a CAMI-compliant form, for use in a Docker
#                           container
#
#   Written in 2015 by Johannes Dröge johannes.droege@uni-duesseldorf.de
#
#   To the extent possible under law, the author(s) have dedicated all copyright
#   and related and neighboring rights to this software to the public domain
#   worldwide. This software is distributed without any warranty.
#
#   You should have received a copy of the CC0 Public Domain Dedication along
#   with this software. If not, see
#   http://creativecommons.org/publicdomain/zero/1.0/

set -o errexit
set -o nounset

required_programs="ncbitax2sqlite tax2racol confusion-matrix cmat2camistats fasta-seqlen"
# Check for required programs
for cmd in $required_programs; do
  if test -z "$(which "$cmd")"; then
    echo "'$cmd' not found in PATH."
    exit 1
  fi
done

# functions
function parse_yaml {  # http://stackoverflow.com/questions/5014632/
  local prefix=$2
  local s='[[:space:]]*' w='[a-zA-Z0-9_]*' fs=$(echo @|tr @ '\034')
  sed -ne "s|^\($s\):|\1|" \
    -e "s|^\($s\)\($w\)$s:$s[\"']\(.*\)[\"']$s\$|\1$fs\2$fs\3|p" \
    -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p"  $1 |
  awk -F$fs '{
    indent = length($1)/2;
    vname[indent] = $2;
    for (i in vname) {if (i > indent) {delete vname[i]}}
    if (length($3) > 0) {
      vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
       printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, $2, $3);
    }
  }'
}

# variables
yamlfile="/bbx/input/biobox.yaml"
ranks='species,genus,family,order,class,phylum,superkingdom'

tmpdir="$(mktemp -d)"
cd "$tmpdir" # go to tmpdir
eval $(parse_yaml "$yamlfile" 'CONT_')

cachedir=""
fastafiles=""
seqlenfile=""
gold_taxfile=""
gold_racolfile=""
pred_taxfile=""
pred_racolfile=""
taxdir=""
taxsqlite=""
cmatfile=""
outtable=""

# check input and ref files


# refresh cache
if [ ! -r "$taxsqlite" -o "$taxdir/names.dmp" -nt "$taxsqlite" -o "$taxdir/nodes.dmp" -nt "$taxsqlite" ]; then
  ncbitax2sqlite.py -dmp "$taxdir" -db "$taxsqlite"
fi

if [ ! -r "$gold_racolfile" -o "$gold_taxfile" -nt "$gold_racolfile" ]; then
  tax2racol.py -t "$sqlitefile" -ranks "$ranks" < "$gold_taxfile" > "$gold_racolfile"
fi

if [ ! -r "$seqlenfile" ]; then
  cat $fastafiles | fasta-seqlen > "$seqlenfile"
else
  for fasta in "$fastafiles"; do
    if [ "$fasta" -nt "$seqlenfile" ]; then
      cat $fastafiles | fasta-seqlen > "$seqlenfile"
      break
    fi
  done
fi

# generate intermediate files
tax2racol.py -t "$sqlitefile" -ranks "$ranks" < "$pred_taxfile" > "$pred_racolfile"
confusion-matrix --rows "$gold_racolfile" --columns "$pred_racolfile" --weights "$seqlenfile" --matrix-form quadratic --allow-missing-columns > "$cmatfile"

# write CAMI stats
cmat2camistats < "$cmatfile" > "$outtable"

# cleanup
test -n "$tmpdir" && rm -r "$tmpdir"

