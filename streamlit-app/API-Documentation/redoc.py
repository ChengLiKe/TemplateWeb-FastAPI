#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import streamlit as st
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()
import os

# 读取配置
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))

# st.set_page_config(page_title="Redoc - API Documentation", page_icon="🐮")
# st.sidebar.header("Redoc - API Documentation")

REDOC_URL = f"http://{HOST}:{PORT}/redoc"
# 使用 iframe 嵌入 FastAPI 文档
st.components.v1.html(f"""
            <iframe 
                src="{REDOC_URL}" 
                width="100%" 
                height="800" 
                frameborder="0">
            </iframe>
        """, height=800)
