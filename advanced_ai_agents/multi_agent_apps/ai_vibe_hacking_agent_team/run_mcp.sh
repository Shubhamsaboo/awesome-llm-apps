#!/bin/bash

for file in src/tools/mcp/*.py; do
  gnome-terminal -- bash -c "python3 $file; exec bash"
done
