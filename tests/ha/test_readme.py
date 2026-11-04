"""Le README ne cite que des services qui existent, et les cite tous."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_services_cites_dans_le_readme_existent():
    services = set(yaml.safe_load((ROOT / "custom_components/screen_time_wallet/services.yaml").read_text(encoding="utf-8")))
    cited = set(re.findall(r"screen_time_wallet\.(\w+)", (ROOT / "README.md").read_text(encoding="utf-8")))
    assert cited == services
