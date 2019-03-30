import re
from collections import OrderedDict
from typing import Dict, List, NamedTuple


# defined for search
class VerseLoc(NamedTuple):
    "Location of a verse within a book"
    chapter: int
    verse: int


class Citation(NamedTuple):
    "Uninterrupted paragraph of scripture, may cross the boundary of chapter"
    start: VerseLoc
    end: VerseLoc


class BookCitations(NamedTuple):
    book: str
    citations: List[Citation]


def parse_citations(citations: str) -> Dict[str, BookCitations]:
    "parse citations to Dict[citation, List[BookCitation]]"

    result: Dict[str, BookCitations] = OrderedDict()

    book_cites_list = re.split(r"[;；]", citations)
    for book_cites in book_cites_list:
        book_cites = (
            book_cites.replace("～", "-")
            .replace("－", "-")
            .replace("_", "-")
            .replace("，", ",")
            .replace("、", ",")
            .replace("：", ":")
            .replace("　", "")
            .replace(" ", "")
        )

        # 1. book
        m = re.search(r"^(?P<book>[^0-9 ]+)\s*", book_cites)
        if m:
            book = m.group("book")
            cites_start = len(book)
            cites = book_cites[cites_start:]
        else:
            cites = book_cites
            book_cites = book + cites

        # 2. citations
        # 11:12-15,19 => Citation((11,12), (11,15)), Citation((11,19),(11,19))
        # 11:12-13:15,19 => Citation((11,12), (13,15)), Citation((13,19),(13,19))
        # 23:10-11,15-17 => Citation((23,10), (23,11)), Citation((23,15),(23,17))
        prev_chapter = -1
        cite_list: List[Citation] = []
        for cite in cites.split(","):
            parts = cite.split("-")
            if len(parts) == 1:  # single verse.
                chv = parts[0].split(":")
                if len(chv) == 1:  # inherit the chapter
                    verse = int(chv[0])
                    chapter = prev_chapter
                else:
                    chapter, verse = map(int, chv)
                    prev_chapter = chapter
                cite_list.append(Citation(VerseLoc(chapter, verse), VerseLoc(chapter, verse)))
            else:
                start, end = parts
                start_parts = list(map(int, start.split(":")))
                if len(start_parts) == 1:
                    start_chapter = prev_chapter
                else:
                    start_chapter = start_parts[0]
                start_verse = start_parts[-1]

                end_parts = list(map(int, end.split(":")))
                if len(end_parts) == 1:
                    end_chapter = start_chapter
                else:
                    end_chapter = end_parts[0]
                prev_chapter = end_chapter
                end_verse = int(end_parts[-1])

                cite_list.append(Citation(VerseLoc(start_chapter, start_verse), VerseLoc(end_chapter, end_verse)))

        result[book_cites] = BookCitations(book, cite_list)

    return result
