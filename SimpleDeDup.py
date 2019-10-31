#!/usr/bin/env python3.7
from code import Importer, Deduplicator
import time

i = Importer("~/Pictures/")
i.run()

d = Deduplicator("~/Pictures/")
d.run()