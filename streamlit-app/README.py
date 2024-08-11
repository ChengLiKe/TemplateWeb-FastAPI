#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import streamlit as st
import os

if not os.path.exists("README.md"):
    st.error("README.md file not found")

with open("README.md", "r", encoding="utf-8") as f:
    md_content = f.read()
    st.markdown(md_content)
