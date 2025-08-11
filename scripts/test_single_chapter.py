#!/usr/bin/env python3
"""Test single chapter processing"""

import os
import sys
import django
from pathlib import Path

sys.path.append('/home/viblio/family_films')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_films.settings')
django.setup()

from batch_d_chapter_processor import BatchDChapterProcessor

def test_single_file():
    processor = BatchDChapterProcessor()
    file_path = Path('/home/viblio/family_films/chapter_sheets/75-SLD_FROS - Baby Jonathan Bathtime Crib and Zoo Visit.xls')
    processor.process_excel_file(file_path)
    processor.print_summary()

if __name__ == "__main__":
    test_single_file()