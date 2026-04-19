#!/usr/bin/env python3
"""
Vietnam Customs 2025 Data Collection - Master Script
Coordinates: captcha solving, PDF downloading, data extraction, and bitable writing.
This script generates a shell script that uses the browser CDP protocol.
"""
import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "2025")
OUTPUT_LINKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_links_2025.json")

print(f"Data directory: {DATA_DIR}")
print(f"Links output: {OUTPUT_LINKS}")
print()
print("STEP 1: Collect PDF links using browser automation")
print("  -> Use browser evaluate to: get captcha -> solve with AI vision -> search each month -> extract links")
print()
print("STEP 2: Download all PDFs using wget")
print()
print("STEP 3: Extract text from PDFs using pdftext")
print()
print("STEP 4: Parse extracted data with Python")
print()
print("STEP 5: Write to bitable")
