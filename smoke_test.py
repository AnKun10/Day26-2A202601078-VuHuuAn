#!/usr/bin/env python3
"""Smoke test — kiểm tra nhanh tầng giao thức MCP của các module KHÔNG cần API key.

Chạy 3 checkpoint không cần key và kiểm tra output có chuỗi mong đợi:
  02-mcp-basics    → weather_client.py      (server/client stdio cơ bản)
  03-production    → registry_client.py     (Tool Registry & Discovery)
  03-production    → versioned_client.py    (Versioning & backward-compat)

Các phần cần API key (01 function calling, 03a auth-server, 04 live chat) KHÔNG
nằm trong smoke test này vì phụ thuộc cấu hình bên ngoài.

Cách chạy (dùng venv gốc đã cài requirements.txt):
    .venv/Scripts/python smoke_test.py      # Windows
    .venv/bin/python smoke_test.py          # macOS/Linux
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

# (nhãn, thư mục chạy, script, các chuỗi PHẢI có trong output)
CHECKS = [
    (
        "02 MCP basics (list_tools + call_tool qua stdio)",
        ROOT / "02-mcp-basics",
        "weather_client.py",
        ["get_weather", "Hanoi: 29°C"],
    ),
    (
        "03b Tool Registry & Discovery",
        ROOT / "03-production",
        "registry_client.py",
        ["Tool Registry", "Best match: get_weather_v2", "get_weather_v2"],
    ),
    (
        "03c Versioning & backward compatibility",
        ROOT / "03-production",
        "versioned_client.py",
        ["weather-v2 v2.0.0", "Deprecated tools", "api_version"],
    ),
]


def run_check(label: str, cwd: Path, script: str, expect: list[str]) -> bool:
    print(f"\n=== {label} ===")
    try:
        proc = subprocess.run(
            [sys.executable, script],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        print("  ❌ TIMEOUT (>60s)")
        return False

    out = proc.stdout + proc.stderr
    if proc.returncode != 0:
        print(f"  ❌ Thoát với mã {proc.returncode}")
        print("  --- output ---")
        print("  " + "\n  ".join(out.strip().splitlines()[-10:]))
        return False

    missing = [s for s in expect if s not in out]
    if missing:
        print(f"  ❌ Thiếu chuỗi mong đợi: {missing}")
        return False

    print(f"  ✅ PASS ({len(expect)}/{len(expect)} chuỗi mong đợi có mặt)")
    return True


def main() -> int:
    print("=" * 60)
    print("MCP Lab — Smoke Test (các phần KHÔNG cần API key)")
    print("=" * 60)

    results = [run_check(*c) for c in CHECKS]

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    if passed == total:
        print(f"✅ TẤT CẢ {total}/{total} checkpoint PASS")
        print("\nGợi ý: chạy thêm các phần cần key —")
        print("  01: export OPENAI_API_KEY=... && python 01-function-calling/weather_function_calling.py")
        print("  03a: python 03-production/auth_server.py  (rồi auth_client.py ở terminal khác)")
        print("  04: xem 04-lab/README.md (uv run adk web)")
        return 0
    print(f"❌ {passed}/{total} checkpoint PASS — xem chi tiết ở trên")
    return 1


if __name__ == "__main__":
    sys.exit(main())
