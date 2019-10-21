#!/usr/bin/env streamit

import pandas as pd
from absl import flags

import streamlit as st
from mvccc.slides import Hymn, Scripture

FLAGS = flags.FLAGS

FLAGS(["streamlit"])

citation = st.text_input("證道經文", "約翰福音14:25")

if citation:
    scriptures = Scripture(citation)
    for _, verses in scriptures.cite_verses.items():
        df = pd.DataFrame(verses)
        df["chapter_verse"] = df["chapter"].astype(str) + ":" + df["verse"].astype(str)
        df.set_index(["chapter_verse"], inplace=True)
        styled = df[["text"]].style.applymap(lambda _: "text-align: left")
        st.table(styled)

memorise = st.text_input("本週金句", "約翰福音3:16")
if memorise:
    scriptures = Scripture(memorise)
    for _, verses in scriptures.cite_verses.items():
        st.table(pd.DataFrame(verses).set_index(["book", "chapter", "verse"]))


messenge = st.text_input("傳講信息")
messenger = st.text_input("證道神仆")
hymn_name = st.text_input("詩班獻詩", "真神羔羊")
hymn = Hymn(hymn_name)
st.write(hymn)
communion = st.checkbox("擘餠喝杯")
download = st.button("下載預覽")
