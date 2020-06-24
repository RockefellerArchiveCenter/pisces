#!/usr/bin/python

import pstats
import sys

stats = pstats.Stats(sys.argv[1])
stats.strip_dirs()
stats.sort_stats('time', 'calls')
stats.print_stats(20)
