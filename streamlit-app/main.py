#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import streamlit as st

pages = {
    "": [
        st.Page("README.py")
    ],
    "API-Documentation": [
        st.Page("API-Documentation/docs.py", title="Docs"),
        st.Page("API-Documentation/redoc.py", title="Redoc"),
        st.Page("API-Documentation/metrics.py", title="Metrics"),
    ],
}

page = st.navigation(pages)
page.run()
