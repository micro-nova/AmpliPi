#!/usr/bin/env python3
"""Patch autoboot.txt boot_partition values after a successful OTA commit."""

import sys
import re

path, new_default, new_tryboot = sys.argv[1], sys.argv[2], sys.argv[3]
content = open(path).read()

content = re.sub(
    r'(\[all\].*?boot_partition=)\d+',
    lambda m: m.group(1) + new_default,
    content, flags=re.DOTALL
)
content = re.sub(
    r'(\[tryboot\].*?boot_partition=)\d+',
    lambda m: m.group(1) + new_tryboot,
    content, flags=re.DOTALL
)

open(path, 'w').write(content)
