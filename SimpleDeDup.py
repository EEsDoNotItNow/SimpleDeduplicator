#!/usr/bin/env python3.7
from code import DB, Logs, Args, ImageCollection, Image
import time

l = Logs()

ic = ImageCollection("~/Pictures/")

# print(len([x for x in ic]))
count = 0
total_bytes = 0
t1 = time.time()
for i in ic:
    t2 = time.time()
    # print(i)
    img = Image(i)
    img.update_from_drive()
    if not img.parsed:
        print(i)
        exit()
    total_bytes += img.size
    count += 1
    print(f"{total_bytes/2**20/(time.time()-t1):,.1f} MiB/s  {count:10}  {(time.time()-t1)/count:.6f}  {time.time()-t2:.6f}")