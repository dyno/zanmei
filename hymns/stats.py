#!/usr/bin/env python

import os
from collections import defaultdict
from os.path import join
from pathlib import Path

from absl import app, logging as log

from comm import TOTAL, init_logging

PROCESSED = Path("processed")
DOWNLOAD = Path("download")


def all_titles():
    d = {}
    for _, _, files in os.walk(DOWNLOAD / "zanmei"):
        for filename in files:
            if not filename.endswith(".png"):
                continue
            idx, name = filename.split("_", 1)
            d[idx] = name[:-4]  # .png

    return d


def has_lyrics():
    d = defaultdict(list)
    for dir_, _, files in os.walk(PROCESSED):
        for filename in files:
            try:
                idx, name = filename.split("_", 1)
                d[idx].append(join(dir_, filename))
            except Exception:
                log.exception(f"exception processing {filename} =>")

    return d


def main(argv):
    del argv
    init_logging()
    titles = all_titles()
    lyrics = has_lyrics()
    for idx in range(1, TOTAL + 1):
        fidx = f"{idx:03d}"
        matches = lyrics.get(fidx, "missing")
        log.info(f"{fidx} = {titles.get(fidx)} => {matches}")


if __name__ == "__main__":
    app.run(main)
