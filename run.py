# -*- coding: utf-8 -*-
"""
@author: @mikegallimore
"""
import argparse

parser = argparse.ArgumentParser()

### creates arguments to make use of in functions
parser.add_argument('season_id', help='Set the season (e.g. 20182019)')

parser.add_argument('--game1', dest='game1', help='Set the value of the 1st game (e.g. 20001) in a range to fetch files for', required=False)
parser.add_argument('--game2', dest='game2', help='Set the 2nd game (e.g. 20002) in a range to fetch files for', required=False)


args = parser.parse_args()


###
### FETCH FILES
###

import files_fetch
files_fetch.parse_ids(args.season_id, args.game1, args.game2)
files_fetch