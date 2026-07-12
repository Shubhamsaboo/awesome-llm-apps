"""
Quick test to verify the repowise install and see distill savings in seconds.
Run this first:  python quick_test.py   (then repowise_demo.py for the full run)
"""

import os
import shutil
import subprocess
import sys
import tempfile


def count_tokens(text: str) -> int:
    try:
        import tiktoken

        try:
            enc = tiktoken.get_encoding("o200k_base")
        except Exception:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 4)


# A small noisy git-log-style command: 40 commit lines, only the summary matters.
NOISE = r'''
import sys
print("commit history (--stat, 40 commits)")
for i in range(40):
    print(f"commit {i:040x}")
    print(f"Author: dev <dev@example.com>")
    print(f"Date:   Mon Jul 7 1{i%10}:00:00 2026 +0000")
    print()
    print(f"    chore: routine change number {i}")
    print()
    print(f" src/module_{i%8}.py | {i % 30 + 1} +++++++--")
    print(f" 1 file changed, {i % 30 + 1} insertions(+)")
    print()
'''


def main() -> None:
    print("REPOWISE QUICK TEST")
    print("=" * 60)

    repowise_bin = shutil.which("repowise")
    if repowise_bin is None:
        print("repowise not found. Install first:\n")
        print("  pip install -r requirements.txt\n")
        sys.exit(1)

    ver = subprocess.run([repowise_bin, "--version"], capture_output=True,
                         text=True, encoding="utf-8", errors="replace")
    print(f"Found: {ver.stdout.strip() or 'repowise'}\n")

    noise_path = os.path.join(tempfile.gettempdir(), "repowise_quicktest_noise.py")
    with open(noise_path, "w", encoding="utf-8") as fh:
        fh.write(NOISE)

    raw = subprocess.run([sys.executable, noise_path], capture_output=True,
                         text=True, encoding="utf-8", errors="replace")
    dist = subprocess.run([repowise_bin, "distill", sys.executable, noise_path],
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")

    raw_tok = count_tokens(raw.stdout)
    dist_tok = count_tokens(dist.stdout)
    pct = (1 - dist_tok / raw_tok) * 100 if raw_tok else 0

    print(f"raw git log output:  {raw_tok:>6,} tokens")
    print(f"repowise distill:    {dist_tok:>6,} tokens")
    print(f"saved:               {raw_tok - dist_tok:>6,} tokens ({pct:.0f}% smaller)\n")

    ok = dist_tok < raw_tok and dist.returncode == 0
    print("Install verified. Run repowise_demo.py for the full demo." if ok
          else "Something looks off, see repowise_demo.py output for detail.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
