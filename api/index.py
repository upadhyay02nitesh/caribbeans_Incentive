"""Vercel entry point.

Vercel's Python runtime imports this file and serves the WSGI callable named
`app`. Everything else is the same application that `python app.py` runs.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402

app = create_app()
