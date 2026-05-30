#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
다중 계정 tmux 런처

.env에 TENNIS_ACCOUNT_N_* 형식으로 계정을 정의하면
각 계정마다 독립 프로세스를 tmux pane/window에서 실행한다.

사용법:
    python3 launch.py              # 전체 계정 예약 실행
    python3 launch.py --test       # 테스트 모드 (대관신청 전 중단)
    python3 launch.py --check      # 로그인 테스트만
    python3 launch.py --dry-run    # tmux 명령 출력만 (미실행)
    python3 launch.py --no-tmux    # tmux 없이 백그라운드 subprocess 실행
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

TMUX_SESSION = "tennis"
SCRIPT_DIR = Path(__file__).parent.resolve()
MAIN_PY = SCRIPT_DIR / "main.py"


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


# ─── tmux 유틸 ────────────────────────────────────────────────────────────────

def tmux_available():
    try:
        subprocess.run(["tmux", "-V"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def tmux_session_exists(session):
    result = subprocess.run(
        ["tmux", "has-session", "-t", session],
        capture_output=True,
    )
    return result.returncode == 0


def tmux_kill_session(session):
    subprocess.run(["tmux", "kill-session", "-t", session], capture_output=True)


def tmux_run(cmd, dry_run=False):
    if dry_run:
        print("  [tmux]", " ".join(str(c) for c in cmd))
        return
    subprocess.run(cmd, check=True)


def build_pane_cmd(account_num, extra_flags):
    """각 pane에서 실행할 셸 명령 문자열."""
    flags = " ".join(extra_flags)
    py = sys.executable
    return (
        f"{py} {MAIN_PY} --account {account_num} {flags}; "
        f"echo ''; "
        f"echo '[계정 {account_num}] 완료. 엔터를 누르면 닫힙니다.'; "
        f"read"
    )


# ─── 레이아웃 ─────────────────────────────────────────────────────────────────

def run_with_tmux(accounts, extra_flags, dry_run=False):
    """tmux 세션을 생성하고 계정별 pane/window를 배치한다.

    1~4개 계정: pane 분할로 한 화면에 모두 표시
    5개 이상:   window 분리 (account 당 1 window)
    """
    cmds = [build_pane_cmd(a["num"], extra_flags) for a in accounts]
    n = len(accounts)

    print(f"[launch] {n}개 계정 → tmux 세션 '{TMUX_SESSION}' 시작")

    # 기존 세션 처리
    if tmux_session_exists(TMUX_SESSION):
        answer = input(f"  이미 '{TMUX_SESSION}' 세션이 있습니다. 종료하고 재시작할까요? [y/N] ").strip().lower()
        if answer == "y":
            tmux_kill_session(TMUX_SESSION)
            if not dry_run:
                time.sleep(0.3)
        else:
            print("[INFO] 기존 세션에 attach합니다.")
            os.execvp("tmux", ["tmux", "attach-session", "-t", TMUX_SESSION])
            return

    if n <= 4:
        _setup_pane_layout(cmds, accounts, dry_run)
    else:
        _setup_window_layout(cmds, accounts, dry_run)

    if not dry_run:
        print(f"[launch] tmux 세션 '{TMUX_SESSION}'에 attach합니다. (Ctrl+B D 로 detach)")
        time.sleep(0.2)
        os.execvp("tmux", ["tmux", "attach-session", "-t", TMUX_SESSION])


def _setup_pane_layout(cmds, accounts, dry_run):
    """1~4개 계정을 pane으로 분할해 한 화면에 표시."""
    n = len(accounts)
    s = TMUX_SESSION

    # 세션 + 첫 번째 pane
    tmux_run([
        "tmux", "new-session", "-d", "-s", s,
        "-n", f"계정{accounts[0]['num']}",
        "bash", "-c", cmds[0],
    ], dry_run)

    if n >= 2:
        # pane 0을 좌우로 분할 → pane 1 (오른쪽)
        tmux_run(["tmux", "split-window", "-t", f"{s}:0.0", "-h",
                  "bash", "-c", cmds[1]], dry_run)

    if n >= 3:
        # pane 0 (왼쪽 위)를 위아래로 분할 → pane 2 (왼쪽 아래)
        tmux_run(["tmux", "split-window", "-t", f"{s}:0.0", "-v",
                  "bash", "-c", cmds[2]], dry_run)

    if n == 4:
        # pane 1 (오른쪽 위)를 위아래로 분할 → pane 3 (오른쪽 아래)
        tmux_run(["tmux", "split-window", "-t", f"{s}:0.1", "-v",
                  "bash", "-c", cmds[3]], dry_run)

    # 크기 균등 정렬
    if n > 1:
        tmux_run(["tmux", "select-layout", "-t", f"{s}:0", "tiled"], dry_run)

    # 첫 번째 pane 포커스
    tmux_run(["tmux", "select-pane", "-t", f"{s}:0.0"], dry_run)

    _print_layout_info(accounts, mode="pane")


def _setup_window_layout(cmds, accounts, dry_run):
    """5개 이상 계정을 window 당 1개로 분리."""
    s = TMUX_SESSION

    # 첫 번째 window
    tmux_run([
        "tmux", "new-session", "-d", "-s", s,
        "-n", f"계정{accounts[0]['num']}",
        "bash", "-c", cmds[0],
    ], dry_run)

    for i, acct in enumerate(accounts[1:], 1):
        tmux_run([
            "tmux", "new-window", "-t", s,
            "-n", f"계정{acct['num']}",
            "bash", "-c", cmds[i],
        ], dry_run)

    # 첫 번째 window 포커스
    tmux_run(["tmux", "select-window", "-t", f"{s}:0"], dry_run)

    _print_layout_info(accounts, mode="window")


def _print_layout_info(accounts, mode):
    print()
    if mode == "pane":
        print("  레이아웃: 단일 화면에 pane 분할")
        print("  단축키:   Ctrl+B → 방향키 (pane 이동)")
    else:
        print("  레이아웃: window 분리")
        print("  단축키:   Ctrl+B N/P (다음/이전 window)")
    print()
    for a in accounts:
        print(f"  계정 {a['num']}: {a['user_id']}")
    print()


# ─── tmux 없을 때 fallback ───────────────────────────────────────────────────

def run_without_tmux(accounts, extra_flags):
    """tmux 미설치 시 각 계정을 백그라운드 subprocess로 실행."""
    print(f"[launch] tmux 없음 — {len(accounts)}개 계정을 백그라운드로 실행합니다.")
    procs = []
    for a in accounts:
        cmd = [sys.executable, str(MAIN_PY), "--account", str(a["num"])] + extra_flags
        log_path = SCRIPT_DIR / f"account_{a['num']}.log"
        with open(log_path, "w") as log_f:
            proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)
        procs.append((a, proc, log_path))
        print(f"  계정 {a['num']} ({a['user_id']}): PID {proc.pid} → {log_path.name}")

    print()
    print("[launch] 모든 프로세스 시작 완료. 종료를 기다립니다...")
    print("         Ctrl+C 로 전체 종료.")
    print()

    try:
        for a, proc, log_path in procs:
            ret = proc.wait()
            status = "성공" if ret == 0 else f"실패(코드 {ret})"
            print(f"  계정 {a['num']} ({a['user_id']}): {status}")
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
                        help="tmux 명령 출력만 (실제 실행 안 함)")
    parser.add_argument("--no-tmux", action="store_true",
                        help="tmux 없이 백그라운드 subprocess로 실행")
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
        print(f"  [{a['num']}] {a['user_id']}")
    print()

    # main.py에 넘길 추가 플래그
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
        print("[dry-run] 실행될 tmux 명령:")
        run_with_tmux(accounts, extra_flags, dry_run=True)
    elif use_tmux:
        run_with_tmux(accounts, extra_flags, dry_run=False)
    else:
        if not args.no_tmux:
            print("[INFO] tmux를 찾을 수 없어 백그라운드 모드로 실행합니다.")
        run_without_tmux(accounts, extra_flags)


if __name__ == "__main__":
    main()
