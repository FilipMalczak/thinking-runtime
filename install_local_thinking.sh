#!/usr/bin/zsh
#This script will install requirements from thinking family from locally checked out repos, overwriting any previous
# installation. Should work with bash too, shebang is aligned with my machine (running Linux Mint).
set -e

here="$(realpath $(dirname $0))"

repos="$HOME/repos"
for r in $(cat ./thinking-dependencies.txt)
do
  #I'm always cloning repos to ~/repos
  project="$repos/$r"
  if [ -d "$project" ]; then
    set -x
    cd $project
    if [ ! -d venv ]; then
      python3 -m venv ./venv
    fi
    set +x
    echo "source ./venv/bin/activate"
    source ./venv/bin/activate
    set -x
    pip install build
    python3 -m build
    artifact=$(ls ./dist | grep '.whl' | sort | tail -1)
    set +x
    source $here/venv/bin/activate
    echo "source $here/venv/bin/activate"
    set -x
    pip uninstall --y "$r"
    pip install "$project/dist/$artifact"
    set +x
  else
    echo "No directory $project present! Clone the repo first!"
    exit 1
  fi
done