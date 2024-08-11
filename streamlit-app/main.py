#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# streamlit_app.py

import streamlit as st
import requests
import os
import time

# 读取配置
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))

# FastAPI 服务器地址
API_URL = f"http://{HOST}:{PORT}/example/get/data"


def fetch_data():
    max_retries = 5
    retry_delay = 2  # seconds
    for attempt in range(max_retries):
        try:
            response = requests.get(API_URL)
            response.raise_for_status()  # 如果响应的状态码不是 200，抛出 HTTPError
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    return {"message": "Failed to fetch data"}


def main():
    st.title("FastAPI and Streamlit Integration")

    data = fetch_data()

    st.write(data.get("message", "No message received"))
    if "data" in data:
        st.line_chart(data["data"])


if __name__ == "__main__":
    main()
