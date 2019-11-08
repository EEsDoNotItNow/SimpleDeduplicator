#!/usr/bin/env python3.7
from code import Importer, Deduplicator, Args
import time

args = Args()

i = Importer("~/Pictures/")
i.run()

d = Deduplicator("~/Pictures/")
d.run()