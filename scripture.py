#!/usr/bin/env python3

import re
import warnings
from collections import OrderedDict, defaultdict
from functools import lru_cache
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
    text: str


class ScriptureIndex(NamedTuple):
    book: str
    chapter: int
    verses: List[int]


def parse_locations(locations: str) -> Dict[str, ScriptureIndex]:
    "parse locations to Dict[loc, ScriptIndex]"
    result: Dict[str, ScriptureIndex] = OrderedDict()

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


def from_ibibles_net(filename: str) -> Bible:
    # XXX: problem with this source is the puctuation is not contemporary.
    def to_record(f: TextIO) -> Generator[BibleVerse, None, None]:
        for line in f:
            if line.startswith(("=", "END")):
                continue
            try:
                parts = line.split(maxsplit=4)
                if len(parts) != 5:
                    log.warning(f"line='{line}' looks missing scripture...")
                    continue
                book = parts[2].replace("列王記", "列王紀").replace("創世紀", "創世記")
                chapter, verse = map(int, parts[3].split(":"))
                yield BibleVerse(book, chapter, verse, parts[-1])
            except Exception:
                log.exception(f"exception processing line: {line}")

    cache = Path(filename + ".csv")
    if cache.exists():
        df = pd.read_csv(cache, sep="\t")

    else:
        # https://stackoverflow.com/questions/17912307/u-ufeff-in-python-string
        with Path(filename).open(encoding="utf-8-sig") as f:
            df = pd.DataFrame.from_records(to_record(f), columns=["book", "chapter", "verse", "text"])
            # if 2 verses merged to 1, use the 1st verse and clear the 2nd.
            warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
            df["text"] = df["text"].str.strip()
            df.loc[df["text"].str.startswith("見上節"), ["text"]] = ""

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

            # <aside epub:type='footnote' id="FN9"><p class="f">
            #   <a class="notebackref" href="#MT6_13"><span class="notemark">*</span> 6:13:</a>
            #   <span class="ft">或譯：脫離惡者</span>
            # </p></aside>
            # <aside epub:type='footnote' id="FN10"><p class="f">
            #   <a class="notebackref" href="#MT6_13"><span class="notemark">*</span> 6:13:</a>
            #   <span class="ft">有古卷沒有因為…阿們等字</span>
            # </p></aside>
            #
            # <aside epub:type='footnote' id="FN33"><p class="f">
            #   <a class="notebackref" href="#MT23_13"><span class="notemark">*</span> 23:13:</a>
            #   <span class="ft">有古卷加：</span>
            #   <span class="fv">14你們這假冒為善的文士和法利賽人有禍了！因為你們侵吞寡婦的家產，假意做很長的禱告，所以要受更重的刑罰。</span>
            # </p></aside>

            ft_notes: Dict[str, List[str]] = defaultdict(list)
            ft_verses: Dict[str, str] = {}

            for aside in book_root.find_all("aside"):
                chv = aside.find("a").text.strip(" *:")

                #   <span class="ft">有古卷加：</span>
                ft = aside.find("span", class_="ft")
                if ft:
                    ft_notes[chv].append(ft.text)

                # <span class="fv">14你們這假冒為善的文士和法利賽人有禍了！因為你們侵吞寡婦的家產，假意做很長的禱告，所以要受更重的刑罰。</span>
                fv = aside.find("span", class_="fv")
                if fv:
                    # move note to the new verse.
                    note = ft_notes[chv].pop()
                    ft_notes[chv].append("")

                    m = re.match(r"(\d+)(.*)", fv.text)
                    assert m, f"the beginning of {fv.text} is supposed to be the verse number."
                    v, text = m.groups()
                    ch = chv.split(":")[0]
                    ft_verses[f"{ch}:{v}"] = f"{note}{text}"

            def to_bible_verse(book, chapter, verse, text, ft_notes):
                chv = f"{chapter}:{verse}"
                if chv in ft_notes:
                    notes = [f"（{note}）" if note else "" for note in ft_notes[chv]]
                    text = text.replace("*", "{}").format(*notes)
                return BibleVerse(book, chapter, verse, text)

            collector: List[str] = []
            for div in book_root.find_all("div", class_=lambda klass: klass in ["p", "q", "m"]):
                for c in div.children:
                    try:
                        if hasattr(c, "class") and c["class"] == ["verse"]:
                            # <span class="verse" id="MT1_12">12 </span>
                            collector = [s for s in collector if s.strip()]
                            if collector:
                                # yield last collected verse
                                yield to_bible_verse(book, chapter, verse, "".join(collector), ft_notes)
                                # check if next verse is a foot note.
                                next_chv = f"{chapter}:{verse+1}"
                                if next_chv in ft_verses:
                                    text = f"（{ft_verses[next_chv]}）"
                                    yield to_bible_verse(book, chapter, verse + 1, text, ft_notes)

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
            yield to_bible_verse(book, chapter, verse, "".join(collector), ft_notes)

    cache = Path(filename + ".csv")
    if cache.exists():
        df = pd.read_csv(cache, sep="\t")
    else:
        with ZipFile(filename) as zf:
            df = pd.DataFrame.from_records(to_record(zf), columns=["book", "chapter", "verse", "text"])
            warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
            df["text"] = df["text"].str.strip()

            df.to_csv(cache, sep="\t", index=False)

    df.set_index(["book", "chapter", "verse"], inplace=True)
    df.index = pd.MultiIndex.from_tuples(df.index)

    return Bible("上帝", df)


@lru_cache()
def scripture(filename=None, source=None) -> Bible:
    if filename is None:
        filename = FLAGS.bible_text
    if source is None:
        source = FLAGS.bible_source

    return {"ibibles.net": from_ibibles_net, "bible.cloud": from_bible_cloud}[source](filename)


def search(bible: Bible, locations: str, word_god=None) -> Dict[str, List[BibleVerse]]:
    if word_god is None:
        word_god = FLAGS.bible_word_god
    loc_list = parse_locations(locations)

    result: Dict[str, List[BibleVerse]] = OrderedDict()
    for loc, scripture_index in loc_list.items():
        df = bible.df.loc[scripture_index]
        verses = []
        for t in df.itertuples():
            book, chapter, verse = t.Index
            text = t.text.replace(bible.word_god, word_god) if word_god != bible.word_god else t.text
            verses.append(BibleVerse(book, chapter, verse, text))
        result[loc] = verses

    return result


def main(argv):
    del argv
    bible = scripture()
    result = search(bible, FLAGS.bible_index)
    for loc, verses in result.items():
        print(loc)
        for v in verses:
            print(f"{v.verse:>3d} {v.text}")
        print()


if __name__ == "__main__":
    app.run(main)
