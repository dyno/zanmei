import json
from collections import defaultdict
from pathlib import Path
from typing import Dict

import attr
from absl import logging as log


@attr.s
class Lyrics:
    title: str = attr.ib()  # 標題
    paragraphs: Dict[str, list] = attr.ib()  # 段落
    end: str = attr.ib(default="")  # 阿門

    def paragraphs_text_only(self):
        pass


DOWNLOAD = Path("download/tmp")


def parse_raw_text(raw_text, title, index):
    paragraphs = defaultdict(list)
    paragraph = []
    state = "paragraph"
    lines = (line.strip() for line in map(str.strip, raw_text.splitlines()))
    for line in lines:
        # pararaph is divided by empty line
        if not line:
            state = "paragraph"
            paragraph = []
            paragraphs["paragraph"].append(paragraph)
            continue

        if line.startswith("副歌"):
            state = "refrain"
            refrain = []
            paragraphs["refrain"].append(refrain)
            continue

        if line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
            state = "paragraph"
            paragraph.append(line[2:].strip())
        else:
            if state == "paragraph":
                paragraph.append(line)
            else:
                refrain.append(line)

    for k in paragraphs:
        paragraphs[k] = list(filter(None, paragraphs[k]))

    lyrics = Lyrics(title, paragraphs)
    d = attr.asdict(lyrics)
    json_path = DOWNLOAD / f"{index:03d}_{title}.json"
    log.info(f"write structured lyrics to {json_path}")
    with json_path.open("w") as out:
        json.dump(d, out, indent=4)
