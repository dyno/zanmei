#!/usr/bin/env python3

import re
import warnings
from collections import OrderedDict, defaultdict, namedtuple
from functools import lru_cache
from itertools import islice
from pathlib import Path
from typing import Dict, Generator, List, NamedTuple, TextIO
from zipfile import ZipFile

import pandas as pd
from absl import app, flags, logging as log
from bs4 import BeautifulSoup

flags.DEFINE_string("bible_text", "download/CMNUNV.epub", "see Makefile for source of download")
flags.DEFINE_string("bible_source", "bible.cloud", "[ibibles.net, bible.cloud]")
flags.DEFINE_string("bible_index", "約翰福音3:16;14:6", "bible search by location")
flags.DEFINE_string("bible_word_god", "\u3000神", "\u3000神 or 上帝")

FLAGS = flags.FLAGS


class Bible(NamedTuple):
    word_god: str
    df: pd.DataFrame


class BibleVerse(NamedTuple):
    book: str
    chapter: int
    verse: int
    scripture: str


def from_bibles_net(filename: str) -> Bible:
    # XXX: problem with this source is the puctuation is not contemporary.
    def to_record(f: TextIO) -> Generator[BibleVerse, None, None]:
        for line in f:
            if line.startswith(("=", "END")):
                continue
            try:
                parts = line.split(maxsplit=4)
                book = parts[2].replace("列王記", "列王紀").replace("創世紀", "創世記")
                chapter, verse = map(int, parts[3].split(":"))
                yield BibleVerse(book, chapter, verse, parts[-1])
            except Exception as e:
                log.exception(f"exception processing line: {line}")

    cache = Path(filename + ".csv")
    if cache.exists():
        df = pd.read_csv(cache, sep="\t")

    else:
        # https://stackoverflow.com/questions/17912307/u-ufeff-in-python-string
        with Path(filename).open(encoding="utf-8-sig") as f:
            df = pd.DataFrame.from_records(to_record(f), columns=["book", "chapter", "verse", "scripture"])
            # if 2 verses merged to 1, use the 1st verse and clear the 2nd.
            warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
            df["scripture"] = df["scripture"].str.strip()
            df.loc[df["scripture"].str.startswith("見上節"), ["scripture"]] = ""

            df.to_csv(cache, sep="\t", index=False)

    df.set_index(["book", "chapter", "verse"], inplace=True)
    df.index = pd.MultiIndex.from_tuples(df.index)
    df.dropna(inplace=True)

    return Bible("\u3000神", df)


def from_bible_cloud(filename: str) -> Bible:
    def to_record(zf: ZipFile) -> Generator[BibleVerse, None, None]:
        index = zf.read("OEBPS/index.xhtml").decode("utf-8-sig")
        root = BeautifulSoup(index, features="lxml")
        for a in root.select("a.oo") + root.select("a.nn"):
            book = a.text
            log.info(f"processing {book}")
            book_text = zf.read(f"OEBPS/{a['href']}").decode("utf-8-sig")
            book_root = BeautifulSoup(book_text, features="lxml")

            # <aside epub:type="footnote" id="FN1"><p class="f">
            #   <a class="notebackref" href="#MT1_1"><span class="notemark">*</span> 1:1:</a>
            #   <span class="ft">後裔，子孫：原文是兒子；下同</span>
            # </p></aside>
            note_list = [
                (aside.find("a").text.strip(" *:"), aside.find("span", class_="ft").text)
                for aside in book_root.find_all("aside")
            ]
            notes: Dict[str, List[str]] = defaultdict(list)
            for ch_ver, note in note_list:
                notes[ch_ver].append(note)

            def to_bible_verse(book, chapter, verse, scripture, notes):
                chv = f"{chapter}:{verse}"
                if chv in notes:
                    scripture = scripture.replace("*", "（{}）").format(*notes[chv])
                return BibleVerse(book, chapter, verse, scripture)

            collector = []
            for div in book_root.find_all("div", class_=lambda klass: klass in ["p", "q", "m"]):
                for c in div.children:
                    try:
                        if hasattr(c, "class") and c["class"] == ["verse"]:
                            # <span class="verse" id="MT1_12">12 </span>
                            collector = [s for s in collector if s.strip()]
                            if collector:
                                # yield last collected verse
                                yield to_bible_verse(book, chapter, verse, "".join(collector), notes)
                            # next verse
                            chapter = int(c["id"][2:].split("_")[0])
                            # <span class="verse" id="MT1_21">21 </span>
                            verse = int(c.text.strip("\xa0").split("-")[0])
                            collector = []
                        elif hasattr(c, "text"):
                            collector.append(c.text)
                        else:  # NavigableString
                            collector.append(str(c))
                    except Exception:
                        log.exception(f"exception processing div={div}")

            # last verse of book
            yield to_bible_verse(book, chapter, verse, "".join(collector), notes)

    cache = Path(filename + ".csv")
    if cache.exists():
        df = pd.read_csv(cache, sep="\t")
    else:
        with ZipFile(filename) as zf:
            df = pd.DataFrame.from_records(to_record(zf), columns=["book", "chapter", "verse", "scripture"])
            warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
            df["scripture"] = df["scripture"].str.strip()

            df.to_csv(cache, sep="\t", index=False)

    df.set_index(["book", "chapter", "verse"], inplace=True)
    df.index = pd.MultiIndex.from_tuples(df.index)

    return Bible("上帝", df)


@lru_cache()
def scripture(filename=None, source=None):
    if filename is None:
        filename = FLAGS.bible_text
    if source is None:
        source = FLAGS.bible_source

    return {"ibibles.net": from_bibles_net, "bible.cloud": from_bible_cloud}[source](filename)


ScriptureIndex = namedtuple("ScriptureIndex", ["book", "chapter", "verses"])


def parse_locations(locations: str) -> Dict[str, ScriptureIndex]:
    """
    >>> from pprint import pprint
    >>> pprint(parse_locations("撒母耳記上 17:31-49")) # 2019-02-24 #doctest: +NORMALIZE_WHITESPACE
    OrderedDict([('撒母耳記上17:31-49',
              ScriptureIndex(book='撒母耳記上', chapter=17, verses=[31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49]))])
    >>> pprint(parse_locations("哥林多前書 6:12-13;10:23-24、31")) # 2019-03-03 #doctest: +NORMALIZE_WHITESPACE
    OrderedDict([('哥林多前書6:12-13',
              ScriptureIndex(book='哥林多前書', chapter=6, verses=[12, 13])),
             ('哥林多前書10:23-24,31',
              ScriptureIndex(book='哥林多前書', chapter=10, verses=[23, 24, 31]))])
    >>> pprint(parse_locations("約翰壹書 2:20, 24-27")) # 2019-03-10 #doctest: +NORMALIZE_WHITESPACE
    OrderedDict([('約翰壹書2:20,24-27',
              ScriptureIndex(book='約翰壹書', chapter=2, verses=[20, 24, 25, 26, 27]))])
    >>> pprint(parse_locations("馬可福音 10:32-45")) # 2019-03-17 #doctest: +NORMALIZE_WHITESPACE
    OrderedDict([('馬可福音10:32-45',
              ScriptureIndex(book='馬可福音', chapter=10, verses=[32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45]))])
    >>> pprint(parse_locations("馬太福音 25：14-30")) # 2019-03-24 #doctest: +NORMALIZE_WHITESPACE
    OrderedDict([('馬太福音25:14-30',
              ScriptureIndex(book='馬太福音', chapter=25, verses=[14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]))])
    """
    result = OrderedDict()

    loc_list = re.split(r"[;；]", locations)
    prev_book = None
    for loc in loc_list:
        # normalize location <book>chapter:verse-verse,verse;chapter:verse
        loc = (
            loc.replace("～", "-")
            .replace("－", "-")
            .replace("，", ",")
            .replace("、", ",")
            .replace("：", ":")
            .replace("　", "")
            .replace(" ", "")
        )

        # 1. book
        # use 約翰一書 not 約翰1書
        m = re.search(r"^(?P<book>[^0-9 ]+)\s*", loc)
        if m:
            book = m.group("book")
            prev_book = book
            chapter_verses = loc[len(book) :]
        else:
            assert prev_book is not None
            book = prev_book
            chapter_verses = loc
            loc = book + chapter_verses

        # 2. chapter
        # 11:12-15,19
        parts = chapter_verses.strip().split(":")
        chapter = int(parts[0])
        ranges = parts[1]

        # 3. verses
        verses = []
        for r in ranges.split(","):
            parts = r.split("-")
            if len(parts) == 1:
                verses.append(int(parts[0]))
            else:
                l, r = map(int, parts)
                verses.extend([i for i in range(l, r + 1)])

        result[loc] = ScriptureIndex(book, chapter, verses)

    return result


def search(bible: Bible, locations: str, word_god=None) -> Dict[str, List[BibleVerse]]:
    if word_god is None:
        word_god = FLAGS.bible_word_god
    loc_list = parse_locations(locations)

    result = OrderedDict()
    for loc, scripture_index in loc_list.items():
        df = bible.df.loc[scripture_index]
        verses = []
        for t in df.itertuples():
            book, chapter, verse = t.Index
            scripture = t.scripture.replace(bible.word_god, word_god) if word_god != bible.word_god else t.scripture
            verses.append(BibleVerse(book, chapter, verse, scripture))
        result[loc] = verses

    return result


def main(argv):
    del argv
    bible = scripture()
    with pd.option_context("display.unicode.east_asian_width", True, "display.max_colwidth", 200):
        result = search(bible, FLAGS.bible_index)
        for loc, verses in result.items():
            print(loc)
            for v in verses:
                print(f"{v.verse:>3d} {v.scripture}")
            print()


if __name__ == "__main__":
    app.run(main)
