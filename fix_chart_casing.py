#!/usr/bin/env python3
"""Fix chart builder tests to expect title-cased column names."""

import re
from pathlib import Path

def fix_line_chart_tests():
    """Fix line_chart_builder tests."""
    file_path = Path("tests/test_line_chart_builder.py")
    content = file_path.read_text()

    # Fix assertions that check for lowercase keys in data
    # Pattern: assert config.data[0]['lowercase']
    content = re.sub(r"assert config\.data\[0\]\['month'\]", "assert config.data[0]['Month']", content)
    content = re.sub(r"assert config\.data\[0\]\['sales'\]", "assert config.data[0]['Sales']", content)
    content = re.sub(r"assert config\.data\[0\]\['revenue'\]", "assert config.data[0]['Revenue']", content)
    content = re.sub(r"assert config\.data\[0\]\['y'\]", "assert config.data[0]['Y']", content)
    content = re.sub(r"assert config\.data\[0\]\['date'\]", "assert config.data[0]['Date']", content)
    content = re.sub(r"assert 'timestamp' in config\.data\[0\]", "assert 'Timestamp' in config.data[0]", content)

    # Fix line dataKey assertions
    content = re.sub(r"assert lines\[0\]\['dataKey'\] == 'revenue'", "assert lines[0]['dataKey'] == 'Revenue'", content)
    content = re.sub(r"assert lines\[0\]\['dataKey'\] == 'y'", "assert lines[0]['dataKey'] == 'Y'", content)

    file_path.write_text(content)
    print(f"✅ Fixed {file_path}")

def fix_bar_chart_tests():
    """Fix bar_chart_builder tests."""
    file_path = Path("tests/test_bar_chart_builder.py")
    if not file_path.exists():
        return

    content = file_path.read_text()

    # Fix assertions that check for lowercase keys
    content = re.sub(r"assert config\.data\[0\]\['category'\]", "assert config.data[0]['Category']", content)
    content = re.sub(r"assert config\.data\[0\]\['value'\]", "assert config.data[0]['Value']", content)
    content = re.sub(r"assert config\.data\[0\]\['revenue'\]", "assert config.data[0]['Revenue']", content)
    content = re.sub(r"assert config\.data\[0\]\['cost'\]", "assert config.data[0]['Cost']", content)

    # Fix bar dataKey assertions
    content = re.sub(r"assert bars\[0\]\['dataKey'\] == 'value'", "assert bars[0]['dataKey'] == 'Value'", content)
    content = re.sub(r"assert bars\[0\]\['dataKey'\] == 'revenue'", "assert bars[0]['dataKey'] == 'Revenue'", content)

    file_path.write_text(content)
    print(f"✅ Fixed {file_path}")

if __name__ == "__main__":
    fix_line_chart_tests()
    fix_bar_chart_tests()
