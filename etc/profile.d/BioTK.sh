export LANG=C
export LC_COLLATE=C
export LC_ALL=C

export BTK_DATA=$HOME/data
export TMPDIR=$HOME/.cache/BioTK/tmpdir/
mkdir -p $TMPDIR

export NCPU=$(grep -c processor /proc/cpuinfo)
export BUFFER_SIZE="2%"

export PYTHONPATH="$PYTHONPATH":$(realpath $(dirname $0))
