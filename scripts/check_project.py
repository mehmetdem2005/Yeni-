from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str

    def as_dict(self) -> dict[str, object]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


def run(command: list[str], cwd: Path = ROOT, timeout: int = 90) -> CheckResult:
    label = " ".join(command)
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
        output = result.stdout.strip()[-1800:]
        return CheckResult(label, result.returncode == 0, output or f"exit={result.returncode}")
    except FileNotFoundError as exc:
        return CheckResult(label, False, f"Komut bulunamadı: {exc}")
    except subprocess.TimeoutExpired:
        return CheckResult(label, False, f"Zaman aşımı: {timeout}s")


def check_file(path: str) -> CheckResult:
    file_path = ROOT / path
    return CheckResult(f"file:{path}", file_path.exists(), "var" if file_path.exists() else "yok")


def main() -> int:
    checks: list[CheckResult] = []

    required_files = [
        "src/crypto_paper_bot/api_server.py",
        "src/crypto_paper_bot/services.py",
        "src/crypto_paper_bot/worker.py",
        "src/crypto_paper_bot/automation_controller.py",
        "src/crypto_paper_bot/database_adapter.py",
        "src/crypto_paper_bot/storage.py",
        "src/crypto_paper_bot/postgres_storage.py",
        "supabase/schema.sql",
        "render.yaml",
        "frontend/package.json",
        "frontend/app/page.tsx",
        "frontend/app/charts/page.tsx",
        "frontend/app/portfolio/page.tsx",
        "frontend/app/logs/page.tsx",
        "frontend/app/news/page.tsx",
        "frontend/app/settings/page.tsx",
        "frontend/app/assistant/page.tsx",
    ]
    checks.extend(check_file(path) for path in required_files)

    checks.append(run([sys.executable, "-m", "compileall", "-q", "src", "scripts"], timeout=120))
    checks.append(run([sys.executable, "scripts/smoke_cloud_runtime.py"], timeout=120))

    if (FRONTEND / "node_modules").exists():
        checks.append(run(["npm", "run", "build"], cwd=FRONTEND, timeout=180))
    else:
        checks.append(CheckResult("npm run build", True, "Atlandı: frontend/node_modules yok. Önce cd frontend && npm install çalıştır."))

    ok = all(item.ok for item in checks)
    payload = {
        "ok": ok,
        "root": str(ROOT),
        "python": sys.version.split()[0],
        "database_url_present": bool(os.environ.get("DATABASE_URL")),
        "checks": [item.as_dict() for item in checks],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
