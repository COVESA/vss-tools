#!/bin/bash -e

# Copyright (C) 2021, COVESA
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

[ -z "$1" ] && { echo "Usage: $0 <input-csv-file>" ; exit 1 ; }

csvfile="$1"
pdffile="$(echo "$1" | sed 's/\.csv/.pdf/')"
hash=$(git rev-parse HEAD)
PROJDIR="$(dirname "$0")/../.."  # Relative to vss-tools/contrib
version=$(cat "$PROJDIR/VERSION")

# Some PDF magic.  Set A4 and landscape mode...
header="
\usepackage{scrextend}
  \usepackage[english]{babel} 
  \usepackage[utf8]{inputenc} 
  \usepackage[a4paper, landscape,top=2.5cm, bottom=2.5cm, left=2.5cm, right=2.5cm]{geometry} 
"

cat <<EOT | pandoc -H <(echo $header) -r csv -w pdf -o "$pdffile"
$(head -1 "$csvfile")
-------------------------------------------------------------------------------------------------------------------------------------------------
GENERATED FROM VSS STANDARD CATALOG $version ($hash)
-------------------------------------------------------------------------------------------------------------------------------------------------
$(tail -n +2 "$csvfile")
EOT

if [ $? -ne 0 ] ; then
  echo "Something went wrong :-("
else
  echo "Wrote $pdffile"
fi
