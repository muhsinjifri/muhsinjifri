#!/bin/bash
# Regenerate every card in ../assets (light + dark). Edit cards.py / header.py, then run this.
cd "$(dirname "$0")" && python3 header.py ../assets && python3 cards.py icons img ../assets
