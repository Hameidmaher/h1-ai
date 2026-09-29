#!/usr/bin/env python3
"""H1-AI Desktop — Native App"""
import webview

URL = "https://h.tailc0256.ts.net/admin"

if __name__ == "__main__":
    webview.create_window(
        title="H1-AI — مساعد الصيدلية",
        url=URL,
        width=1400, height=900,
        min_size=(800, 600),
    )
    webview.start(debug=False)
