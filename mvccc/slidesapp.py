#!/usr/bin/env streamlit

import hashlib
from io import StringIO

import pandas as pd
from absl import flags
from pptx import Presentation

import streamlit as st
from mvccc.slides import Hymn, mvccc_slides, next_sunday, search_hymn_ppt, to_pptx, to_scripture

FLAGS = flags.FLAGS

FLAGS(["streamlit"])


def pick_hymn(keyword: str, label: str) -> Hymn:
    hymns = search_hymn_ppt(keyword=keyword)
    hymn = st.radio("", hymns, index=0, format_func=lambda h: h.filename)
    sio = StringIO()
    for _, (title, lines) in hymn.lyrics:
        sio.write(f"\n#{title[0].strip('#')}\n")
        sio.write("\n".join(lines))
        sio.write("\n")
    st.markdown(f"```\n{sio.getvalue()}\n```")

    return hymn


message = st.text_input("主日信息", "我必不至缺乏")

messager = st.text_input("證道神仆", "劉志信牧师")

citation = st.text_input("證道經文", "詩篇23:1-6")

if citation:
    scriptures = to_scripture(citation)
    for _, verses in scriptures.cite_verses.items():
        df = pd.DataFrame(verses)
        df["chapter_verse"] = df["chapter"].astype(str) + ":" + df["verse"].astype(str)
        df.set_index(["chapter_verse"], inplace=True)
        styled = df[["text"]].style.applymap(lambda _: "text-align: left")
        st.table(styled)

memorise = st.text_input("本週金句", "詩篇23:1")
if memorise:
    scriptures = to_scripture(memorise)
    for _, verses in scriptures.cite_verses.items():
        st.table(pd.DataFrame(verses).set_index(["book", "chapter", "verse"]))

choir = None
label = "詩班獻詩"
keyword = st.text_input(label, "真神羔羊")
if keyword.strip():
    choir = pick_hymn(keyword, label=label)

hymns = []
for i in range(4):
    label = f"敬拜赞美 - {i+1}"
    keyword = st.text_input(label, "耶和華")
    if keyword.strip():
        picked = pick_hymn(keyword, label)
        hymns.append(picked)

response = None
label = "回應詩歌"
keyword = st.text_input(label, "耶和華你是我的神")
if keyword.strip():
    response = pick_hymn(keyword, label)

offering = None
label = "奉獻詩歌"
keyword = st.text_input(label, "獻上感恩的心")
if keyword.strip():
    offering = pick_hymn(keyword, label)

coming_sunday = next_sunday()
is_first_week = int(coming_sunday[-2]) + int(coming_sunday[-1]) <= 7
communion = st.checkbox("擘餠喝杯", value=is_first_week)

deck = mvccc_slides(
    hymns=[h.filename for h in hymns],
    scripture=citation,
    memorize=memorise,
    message=message,
    messager=messager,
    choir=choir.filename if choir else "",
    response=response.filename if response else "",
    offering=offering.filename if offering else "",
    communion=communion,
)

download = st.button("下載預覽")
if download:
    master = Presentation(FLAGS.master_pptx)
    ppt = to_pptx(deck, master)
    output_filename = f"{coming_sunday}.pptx"
    ppt.save(output_filename)
    st.markdown(f"[{output_filename}](/zanmei/{output_filename})")
