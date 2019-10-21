#!/usr/bin/env streamit

import streamlit as st

#  --choir=我寧願有耶穌
#
#  --hymns=榮耀歸於天父
#  --hymns=教會唯一的根基
#  --hymns=愛的真諦
#  --hymns=在每一個家庭中
#  --response=愛使我們合一
#  --offering=我奉獻所有
#
#  --scripture=哥林多前書13:4-7
#  --memorize=箴言19:11
#  --message=寬恕之愛
#  --messager=卓爾君 牧師

"""
## 主日敬拜
"""

"""
### 詩班獻詩
"""
choir = st.text_input("")

"""
### 敬拜詩歌
"""

# bible

"""
### 引用經文
"""
citation = st.text_input("")

"""
### 本週金句
"""
memorise = st.text_input("")

"""
### 傳講信息
"""
messenge = st.text_input("")

"""
### 證道牧師
"""
messenger = st.text_input("")

"""
### 擘餠喝杯
"""
communion = st.checkbox("")

download = st.button("下載預覽")
