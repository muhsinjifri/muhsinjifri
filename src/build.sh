#!/bin/bash
# Regenerate every card in ../assets (light + dark). Edit cards.py, then run this.
cd "$(dirname "$0")" && python3 cards.py icons img ../assets
