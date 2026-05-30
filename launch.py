#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
다중 계정 tmux 런처

.env에 TENNIS_ACCOUNT_N_* 형식으로 계정을 정의하면
GROUP_SIZE(기본 4)개씩 묶어 그룹마다 새 터미널 창을 열고
그 안에서 tmux 세션을 시작해 pane으로 분할 표시한다.

  계정 13개 예시:
    그룹 1 (계정 1~4)  → 새 터미널 창 → tmux tennis_1 → 2×2 pane
    그룹 2 (계정 5~8)  → 새 터미널 창 → tmux tennis_2 → 2×2 pane
    그룹 3 (계정 9~12) → 새 터미널 창 → tmux tennis_3 → 2×2 pane
    그룹 4 (계정 13)   → 새 터미널 창 → tmux tennis_4 → 1 pane

사용법:
    python3 launch.py                  # 기본 실행 (4개씩 그룹)
    python3 launch.py --group-size 2   # 터미널 창당 최대 2개
    python3 launch.py --test           # 테스트 모드 (대관신청 전 중단)
    python3 launch.py --check          # 로그인 테스트만
    python3 launch.py --dry-run        # 스크립트 내용 출력 (창 미생성)
    python3 launch.py --no-tmux        # tmux 없이 백그라운드 subprocess 실행
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

GROUP_SIZE = 4                   # 터미널 창당 최대 pane 수
TMUX_SESSION_PREFIX = "tennis"   # 세션 이름: tennis_1, tennis_2, ...
SCRIPT_DIR = Path(__file__).parent.resolve()
MAIN_PY = SCRIPT_DIR / "main.py"
TMP_DIR = Path("/tmp")

# tmux 절대 경로: iTerm2 새 창의 기본 PATH(/usr/bin:/bin 등)에는
# /opt/homebrew/bin 이 없어서 'tmux: command not found' 가 발생하므로
# 현재 환경에서 경로를 확정해 스크립트에 하드코딩한다.
TMUX_BIN = shutil.which("tmux") or "tmux"


# ─── 계정 파싱 ────────────────────────────────────────────────────────────────

def load_env_file():
    env_file = SCRIPT_DIR / ".env"
    if not env_file.exists():
        return
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                if key not in os.environ:
                    os.environ[key] = value.strip()


def load_accounts():
    """TENNIS_ACCOUNT_N_ID/PW 환경변수에서 계정 목록 반환."""
    accounts = []
    for n in range(1, 100):
        uid = os.environ.get(f"TENNIS_ACCOUNT_{n}_ID", "").strip()
        upw = os.environ.get(f"TENNIS_ACCOUNT_{n}_PW", "").strip()
        if not uid or not upw:
            continue
        accounts.append({"num": n, "user_id": uid})
    return accounts


def chunk_accounts(accounts, size):
    """계정 목록을 size개씩 그룹으로 나눈다."""
    return [accounts[i:i + size] for i in range(0, len(accounts), size)]


# ─── 터미널 앱 감지 ──────────────────────────────────────────────────────────

def detect_terminal_app():
    """사용 가능한 터미널 앱을 감지한다.

    감지 순서: 실행 중인 iTerm2 → 설치된 iTerm2 → Terminal.app
    Returns: 'iterm2' | 'terminal'
    """
    try:
        result = subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to return '
             '(name of every process) contains "iTerm2"'],
            capture_output=True, text=True, timeout=3,
        )
        if result.stdout.strip() == "true":
            return "iterm2"
    except Exception:
        pass

    if Path("/Applications/iTerm.app").exists():
        return "iterm2"

    return "terminal"


# ─── 스크립트 생성 ────────────────────────────────────────────────────────────

def create_group_scripts(group, session_name, extra_flags, group_idx):
    """그룹 tmux 스크립트와 계정별 실행 스크립트를 /tmp에 생성한다.

    생성 파일:
      /tmp/tennis_acct_{N}.sh     — 계정 N 단독 실행 스크립트
      /tmp/tennis_group_{idx}.sh  — tmux 세션 생성 + pane 분할 + attach

    Returns: Path — 그룹 스크립트 경로
    """
    py = sys.executable
    flags_str = " ".join(extra_flags)

    # ── 계정별 실행 스크립트 ──────────────────────────────────────────
    acct_paths = []
    for acct in group:
        path = TMP_DIR / f"tennis_acct_{acct['num']}.sh"
        path.write_text(
            "#!/bin/bash\n"
            f"{py} {MAIN_PY} --account {acct['num']} {flags_str}\n"
            "echo ''\n"
            f"echo '[계정 {acct['num']}] {acct['user_id']} 완료."
            " 엔터를 누르면 닫힙니다.'\n"
            "read\n"
        )
        path.chmod(0o755)
        acct_paths.append(path)

    # ── 그룹 tmux 스크립트 ───────────────────────────────────────────
    n = len(group)
    user_ids = ", ".join(a["user_id"] for a in group)

    # TMUX_BIN: 현재 환경에서 확정한 절대 경로를 스크립트에 하드코딩.
    # iTerm2 새 창은 non-login shell로 실행되어 기본 PATH가
    # /usr/bin:/bin:/usr/sbin:/sbin 뿐이므로 Homebrew tmux를 찾지 못한다.
    lines = [
        "#!/bin/bash",
        f'SESSION="{session_name}"',
        f'TMUX="{TMUX_BIN}"',
        "",
        "# 기존 세션이 있으면 제거",
        '"$TMUX" kill-session -t "$SESSION" 2>/dev/null || true',
        "",
        f"# 그룹 {group_idx}: {user_ids}",
        f'"$TMUX" new-session -d -s "$SESSION" "{acct_paths[0]}"',
    ]

    if n >= 2:
        lines.append(
            f'"$TMUX" split-window -t "$SESSION:0.0" -h "{acct_paths[1]}"'
        )
    if n >= 3:
        lines.append(
            f'"$TMUX" split-window -t "$SESSION:0.0" -v "{acct_paths[2]}"'
        )
    if n >= 4:
        lines.append(
            f'"$TMUX" split-window -t "$SESSION:0.1" -v "{acct_paths[3]}"'
        )

    if n > 1:
        lines.append('"$TMUX" select-layout -t "$SESSION:0" tiled')

    lines += [
        '"$TMUX" select-pane -t "$SESSION:0.0"',
        "",
        "# bash 프로세스를 tmux attach 로 교체 → 터미널 창이 tmux 세션을 직접 표시",
        'exec "$TMUX" attach-session -t "$SESSION"',
    ]

    group_path = TMP_DIR / f"tennis_group_{group_idx}.sh"
    group_path.write_text("\n".join(lines) + "\n")
    group_path.chmod(0o755)

    return group_path


# ─── 터미널 창 열기 ──────────────────────────────────────────────────────────

def open_new_terminal(script_path, terminal_app, dry_run=False):
    """AppleScript로 새 터미널 창을 열고 그룹 스크립트를 실행한다."""
    path_str = str(script_path)

    if terminal_app == "iterm2":
        applescript = (
            'tell application "iTerm2"\n'
            f'    create window with default profile command "bash {path_str}"\n'
            'end tell'
        )
    else:
        # Terminal.app: do script 는 새 창에서 실행됨
        applescript = (
            'tell application "Terminal"\n'
            f'    do script "bash {path_str}"\n'
            '    activate\n'
            'end tell'
        )

    if dry_run:
        indent = "    "
        formatted = applescript.replace("\n", f"\n{indent}")
        print(f"  [osascript]\n    {formatted}")
        return

    subprocess.run(["osascript", "-e", applescript], check=True)


# ─── 멀티 터미널 실행 ────────────────────────────────────────────────────────

def tmux_available():
    try:
        subprocess.run([TMUX_BIN, "-V"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def run_multi_terminal(accounts, extra_flags, group_size, dry_run=False):
    """계정을 group_size개씩 묶어 그룹마다 새 터미널 창 + tmux 세션을 생성한다."""
    groups = chunk_accounts(accounts, group_size)
    terminal_app = detect_terminal_app()
    total = len(groups)

    print(f"[launch] {len(accounts)}개 계정 → {total}개 터미널 창 "
          f"(창당 최대 {group_size}개 pane)")
    print(f"[launch] 터미널 앱: {terminal_app}")
    print()

    for i, group in enumerate(groups, 1):
        session = f"{TMUX_SESSION_PREFIX}_{i}"
        user_ids = [a["user_id"] for a in group]

        print(f"  ── 그룹 {i}/{total}  세션={session}  "
              f"계정={', '.join(user_ids)}")

        # 기존 세션 제거
        if not dry_run:
            subprocess.run(
                [TMUX_BIN, "kill-session", "-t", session], capture_output=True
            )

        # 스크립트 생성
        group_script = create_group_scripts(group, session, extra_flags, i)

        if dry_run:
            print(f"     그룹 스크립트: {group_script}")
            print()
            separator = "     " + "─" * 50
            print(separator)
            for line in group_script.read_text().splitlines():
                print(f"     {line}")
            print(separator)
            open_new_terminal(group_script, terminal_app, dry_run=True)
            print()
            continue

        # 새 터미널 창 열기
        open_new_terminal(group_script, terminal_app, dry_run=False)

        # 창 생성 간격 (마지막 그룹 제외)
        if i < total:
            time.sleep(0.5)

    if not dry_run:
        print()
        print(f"[launch] {total}개 터미널 창 생성 완료.")
        sessions = [f"{TMUX_SESSION_PREFIX}_{i}" for i in range(1, total + 1)]
        print(f"         세션 목록: {', '.join(sessions)}")
        print(f"         재접속:    tmux attach-session -t {TMUX_SESSION_PREFIX}_1")


# ─── tmux 없을 때 fallback ───────────────────────────────────────────────────

def run_without_tmux(accounts, extra_flags):
    """tmux 미설치 시 각 계정을 백그라운드 subprocess + 로그 파일로 실행."""
    print(f"[launch] tmux 없음 — {len(accounts)}개 계정을 백그라운드로 실행합니다.")
    procs = []
    for a in accounts:
        cmd = [sys.executable, str(MAIN_PY), "--account", str(a["num"])] + extra_flags
        log_path = SCRIPT_DIR / f"account_{a['num']}.log"
        with open(log_path, "w") as log_f:
            proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)
        procs.append((a, proc, log_path))
        print(f"  계정 {a['num']:2d} ({a['user_id']}): PID {proc.pid} → {log_path.name}")

    print()
    print("[launch] 모든 프로세스 시작 완료. 종료를 기다립니다...")
    print("         Ctrl+C 로 전체 종료.")
    print()

    try:
        for a, proc, log_path in procs:
            ret = proc.wait()
            status = "성공" if ret == 0 else f"실패(코드 {ret})"
            print(f"  계정 {a['num']:2d} ({a['user_id']}): {status}")
    except KeyboardInterrupt:
        print("\n[launch] 중단 — 모든 프로세스를 종료합니다.")
        for _, proc, _ in procs:
            proc.terminate()


# ─── 진입점 ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="다중 계정 tmux 런처",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
.env 설정 예시:
  TENNIS_ACCOUNT_1_ID=user1
  TENNIS_ACCOUNT_1_PW=pass1
  TENNIS_ACCOUNT_1_RESERVATION_1=2026-06-07:10:1

  TENNIS_ACCOUNT_2_ID=user2
  TENNIS_ACCOUNT_2_PW=pass2
  TENNIS_ACCOUNT_2_RESERVATION_1=2026-06-14:08:3
        """,
    )
    parser.add_argument("--test", action="store_true",
                        help="테스트 모드 (대관신청 전 중단)")
    parser.add_argument("--check", action="store_true",
                        help="로그인 테스트만 실행")
    parser.add_argument("--dry-run", action="store_true",
                        help="생성될 스크립트 내용 출력 (터미널 창 미생성)")
    parser.add_argument("--no-tmux", action="store_true",
                        help="tmux 없이 백그라운드 subprocess로 실행")
    parser.add_argument("--group-size", type=int, default=GROUP_SIZE,
                        metavar="N",
                        help=f"터미널 창당 최대 계정(pane) 수 (기본값: {GROUP_SIZE})")
    args = parser.parse_args()

    load_env_file()
    accounts = load_accounts()

    if not accounts:
        print("[ERROR] 계정이 없습니다.")
        print()
        print("  .env에 다음 형식으로 계정을 추가하세요:")
        print("    TENNIS_ACCOUNT_1_ID=아이디")
        print("    TENNIS_ACCOUNT_1_PW=비밀번호")
        print("    TENNIS_ACCOUNT_1_RESERVATION_1=2026-06-07:10:1")
        print()
        print("  단일 계정 모드는 python3 main.py 를 직접 실행하세요.")
        sys.exit(1)

    print("=" * 60)
    print("고양시 테니스장 다중 계정 런처")
    print("=" * 60)
    print(f"  계정 수: {len(accounts)}개")
    for a in accounts:
        print(f"  [{a['num']:2d}] {a['user_id']}")
    print()

    extra_flags = []
    if args.test:
        extra_flags.append("--test")
        print("  모드: 테스트 (대관신청 전 중단)")
    elif args.check:
        extra_flags.append("--check")
        print("  모드: 로그인 테스트")
    else:
        print("  모드: 실제 예약")
    print()

    use_tmux = not args.no_tmux and tmux_available()

    if args.dry_run:
        run_multi_terminal(accounts, extra_flags,
                           group_size=args.group_size, dry_run=True)
    elif use_tmux:
        run_multi_terminal(accounts, extra_flags,
                           group_size=args.group_size, dry_run=False)
    else:
        if not args.no_tmux:
            print("[INFO] tmux를 찾을 수 없어 백그라운드 모드로 실행합니다.")
        run_without_tmux(accounts, extra_flags)


if __name__ == "__main__":
    main()
