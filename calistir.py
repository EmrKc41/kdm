"""Excel motorunu ve web arayüzünü birlikte başlatır.

    python calistir.py            geliştirme (Next.js dev)
    python calistir.py --uretim   üretim (önce derlenmiş olmalı: npm run build)

Ctrl+C ikisini birden durdurur.
"""

from __future__ import annotations

import argparse
import shutil
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

KOK = Path(__file__).resolve().parent
WEB = KOK / "web"

MOTOR_PORT = 8000
ARAYUZ_PORT = 3000


def npm_komutu() -> str:
    """Windows'ta npm bir .cmd betiğidir; doğrudan çalıştırılamaz."""
    return shutil.which("npm") or ("npm.cmd" if sys.platform == "win32" else "npm")


def kontrol(uretim: bool = False) -> None:
    eksikler = []
    if not (KOK / "templates" / "taslaktalimat.xlsx").is_file():
        eksikler.append("templates/taslaktalimat.xlsx")
    if not (KOK / "templates" / "taslaktne.xlsx").is_file():
        eksikler.append("templates/taslaktne.xlsx")
    if not (WEB / "node_modules").is_dir():
        eksikler.append("web/node_modules  (çözüm: cd web && npm install)")
    if uretim and not (WEB / ".next").is_dir():
        eksikler.append("web/.next  (çözüm: cd web && npm run build)")
    if eksikler:
        print("Başlatılamadı, şunlar eksik:")
        for e in eksikler:
            print("  -", e)
        sys.exit(1)


def main() -> None:
    ayrist = argparse.ArgumentParser(description="Kalite Doküman Merkezi")
    ayrist.add_argument("--uretim", action="store_true", help="derlenmiş sürümü çalıştır")
    ayrist.add_argument("--tarayici", action="store_true", help="tarayıcıyı otomatik aç")
    args = ayrist.parse_args()

    kontrol(args.uretim)
    npm = npm_komutu()
    surecler: list[subprocess.Popen] = []

    try:
        motor_komutu = [
            sys.executable, "-m", "uvicorn", "ui.app:app",
            "--host", "127.0.0.1", "--port", str(MOTOR_PORT),
            "--log-level", "warning",
        ]
        if not args.uretim:
            # Geliştirmede ZORUNLU: uvicorn varsayılan olarak kodu bir kez
            # yükler. --reload olmadan core/ içinde yapılan bir düzeltme
            # sunucu yeniden başlatılana kadar ETKİSİZ kalır; arayüz düzelmiş
            # sanılan bir motordan eski çıktıyı almaya devam eder.
            motor_komutu += ["--reload", "--reload-dir", "core", "--reload-dir", "ui"]

        print(f"  Excel motoru  : http://127.0.0.1:{MOTOR_PORT}"
              f"{'  (otomatik yeniden yükleme açık)' if not args.uretim else ''}")
        surecler.append(subprocess.Popen(motor_komutu, cwd=KOK))

        time.sleep(2)

        komut = [npm, "run", "start" if args.uretim else "dev"]
        print(f"  Web arayüzü   : http://localhost:{ARAYUZ_PORT}\n")
        surecler.append(subprocess.Popen(komut, cwd=WEB))

        if args.tarayici:
            time.sleep(4)
            webbrowser.open(f"http://localhost:{ARAYUZ_PORT}")

        print("  Durdurmak için Ctrl+C\n")
        while all(s.poll() is None for s in surecler):
            time.sleep(0.5)

        for s in surecler:
            if s.poll() is not None and s.returncode != 0:
                print(f"\n  Bir süreç beklenmedik şekilde durdu (kod {s.returncode}).")

    except KeyboardInterrupt:
        print("\n  Durduruluyor…")
    finally:
        for s in surecler:
            if s.poll() is None:
                try:
                    s.send_signal(signal.SIGTERM)
                    s.wait(timeout=5)
                except Exception:
                    s.kill()


if __name__ == "__main__":
    main()
