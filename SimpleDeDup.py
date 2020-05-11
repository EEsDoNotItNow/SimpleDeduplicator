#!/usr/bin/env python3.7
from code import Importer, Deduplicator, Args, NameFix
import time

args = Args()

nf = NameFix("~/Pictures/")
nf.run()

i = Importer("~/Pictures/")
i.run()

d = Deduplicator("~/Pictures/")
d.run()