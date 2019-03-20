#!/usr/bin/env python3

# vim: set fileencoding=utf-8 :

from datetime import date, timedelta
from typing import Generator, List, Tuple

import attr
from absl import app, flags, logging as log

from pptx import Presentation

flags.DEFINE_string("master_pptx", "mvccc_master.pptx", "The template pptx")
flags.DEFINE_string("pptx", "", "The pptx")

FLAGS = flags.FLAGS


def next_sunday() -> str:
    today = date.today()
    sunday = today + timedelta(6 - today.weekday())
    return sunday.isoformat()


def extract_slides_text(ppt: Presentation) -> Generator[Tuple[int, List[str]], None, None]:
    for idx, slide in enumerate(ppt.slides):
        text_list = []  # type: List[str]
        if slide.shapes.title:
            log.debug(f"{slide.shapes.title.text}")
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for paragraph in shape.text_frame.paragraphs:
                text_list.extend([run.text for run in paragraph.runs])
        yield idx, text_list


LAYOUT_PRELUDE = 0
LAYOUT_MESSAGE = 1
LAYOUT_HYMN = 2
LAYOUT_VERSE = 3
LAYOUT_MEMORIZE = 4
LAYOUT_TEACHING = 5
LAYOUT_SECTION = 6
LAYOUT_BLANK = 7


@attr.s
class Prelude:
    message: str = attr.ib()
    picture: str = attr.ib()

    def add_to(self, ppt: Presentation) -> Presentation:
        slide = ppt.slides.add_slide(ppt.slide_layouts[LAYOUT_PRELUDE])
        message, picture = slide.placeholders
        message.text = self.message
        picture.insert_picture(self.picture)

        return ppt


@attr.s
class Message:
    message: str = attr.ib()

    def add_to(self, ppt: Presentation) -> Presentation:
        slide = ppt.slides.add_slide(ppt.slide_layouts[LAYOUT_MESSAGE])
        message, = slide.placeholders
        message.text = self.message

        return ppt


@attr.s
class Hymn:
    title: str = attr.ib()
    lyrics: List[List[str]] = attr.ib()


@attr.s
class Section:
    title: str = attr.ib()

    def add_to(self, ppt: Presentation) -> Presentation:
        slide = ppt.slides.add_slide(ppt.slide_layouts[LAYOUT_SECTION])
        title, = slide.placeholders
        title.text = self.title

        return ppt


@attr.s
class Teaching:
    title: str = attr.ib()
    message: str = attr.ib()
    messenger: str = attr.ib()

    def add_to(self, ppt: Presentation) -> Presentation:
        slide = ppt.slides.add_slide(ppt.slide_layouts[LAYOUT_TEACHING])
        message, = slide.placeholders
        message.text = "\n\n".join([self.title, self.message, self.messenger])

        return ppt


@attr.s
class Memorize:
    verse: str = attr.ib()
    location: str = attr.ib()


@attr.s
class Blank:
    def add_to(self, ppt: Presentation) -> Presentation:
        _ = ppt.slides.add_slide(ppt.slide_layouts[LAYOUT_BLANK])

        return ppt


def mvccc_slides_stack(master_slide: Presentation) -> Presentation:
    ppt = master_slide

    slides = [
        Prelude("  請儘量往前或往中間坐,並將手機關閉或關至靜音,預備心敬拜！", "silence_phone1.png"),
        Message(
            """  惟耶和華在他的聖殿中；
全地的人，都當在他面前肅敬靜默。

            哈巴谷書 2:20"""
        ),
        Section("頌  讚"),
        Section("宣  召"),
        Section("祈  禱"),
        Section("讀  經"),
        Section("獻  詩"),
        Teaching("信息", "「  」", "牧師"),
        Section("回  應"),
        Section("奉 獻 禱 告"),
        Section("歡 迎 您"),
        Section("家 事 分 享"),
        Section("祝  福"),
        Section("默  禱"),
        Blank(),
    ]
    for slide in slides:
        slide.add_to(ppt)

    return ppt


def main(argv):
    del argv

    master = Presentation(FLAGS.master_pptx)
    ppt = mvccc_slides_stack(master)

    for idx, text in extract_slides_text(ppt):
        print(f"{idx+1:02d} {text}")

    if not FLAGS.pptx:
        FLAGS.pptx = f"{next_sunday()}.pptx"
    ppt.save(FLAGS.pptx)


if __name__ == "__main__":
    app.run(main)
