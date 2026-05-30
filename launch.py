#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
다중 계정 런처 — tmux / iTerm2 네이티브 split / Linux 터미널

.env에 TENNIS_ACCOUNT_N_* 형식으로 계정을 정의하면
GROUP_SIZE(기본 4)개씩 묶어 그룹마다 새 터미널 창을 열고
분할 화면으로 표시한다.

플랫폼별 동작:
  macOS  + tmux     : tmux 세션 → iTerm2/Terminal.app 창
  macOS  + --no-tmux: iTerm2 네이티브 split pane / Terminal.app 탭
  Linux  + tmux     : tmux 세션 → 감지된 터미널 에뮬레이터 창
  Linux  + --no-tmux: 계정마다 개별 터미널 창 (분할 없음)
  --background      : 터미널 창 없이 subprocess + 로그 파일

사용법:
    python3 launch.py                  # tmux 세션 + 새 터미널 창 (기본)
    python3 launch.py --no-tmux        # 터미널 네이티브 분할 (tmux 없이)
    python3 launch.py --background     # 백그라운드 subprocess + 로그 파일
    python3 launch.py --group-size 2   # 창당 최대 2개
    python3 launch.py --test           # 테스트 모드 (대관신청 전 중단)
    python3 launch.py --check          # 로그인 테스트만
    python3 launch.py --dry-run        # 실행 내용 출력만 (창 미생성)
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ─── 상수 ─────────────────────────────────────────────────────────────────────

GROUP_SIZE = 4
TMUX_SESSION_PREFIX = "tennis"
SCRIPT_DIR = Path(__file__).parent.resolve()
MAIN_PY = SCRIPT_DIR / "main.py"
TMP_DIR = Path("/tmp")

IS_MACOS = sys.platform == "darwin"

# Linux 터미널 에뮬레이터 감지 우선순위.
# 각 항목: (실행파일명, 명령 빌더 키)
LINUX_TERMINALS = [
    "gnome-terminal",
    "xterm",
    "konsole",
    "xfce4-terminal",
    "alacritty",
    "kitty",
    "terminator",
    "tilix",
    "lxterminal",
    "mate-terminal",
    "rxvt",
]

# iTerm2 새 창은 non-login shell로 실행되어 기본 PATH 가
# /usr/bin:/bin:/usr/sbin:/sbin 뿐이므로 Homebrew tmux 를 찾지 못한다.
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

    macOS:
      실행 중인 iTerm2 → 설치된 iTerm2 → 'terminal' (Terminal.app)
      Returns: 'iterm2' | 'terminal'

    Linux:
      LINUX_TERMINALS 목록을 순서대로 탐색해 첫 번째 발견된 것을 반환.
      Returns: 실행파일명 문자열 (예: 'gnome-terminal') | None
    """
    if IS_MACOS:
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
    else:
        for term in LINUX_TERMINALS:
            if shutil.which(term):
                return term
        return None


def build_linux_open_cmd(terminal, script_path):
    """Linux 터미널 에뮬레이터별 새 창 + 스크립트 실행 명령을 반환한다.

    각 에뮬레이터마다 플래그가 다르므로 이 함수에서 중앙 관리한다.
    """
    path = str(script_path)

    # gnome-terminal 3.x 이후 '-e' 는 deprecated → '--' 로 분리
    if terminal == "gnome-terminal":
        return ["gnome-terminal", "--", "bash", path]

    # xterm / rxvt: -e 뒤에 명령
    if terminal in ("xterm", "rxvt"):
        return [terminal, "-e", "bash", path]

    # konsole: -e 뒤에 명령
    if terminal == "konsole":
        return ["konsole", "-e", "bash", path]

    # xfce4-terminal: -e "명령" (문자열 통째로)
    if terminal == "xfce4-terminal":
        return ["xfce4-terminal", "-e", f"bash {path}"]

    # alacritty: -e 뒤에 명령 (3.0+ 에서 -e → -- 로 변경됐지만 호환 유지)
    if terminal == "alacritty":
        return ["alacritty", "-e", "bash", path]

    # kitty: 직접 명령 전달
    if terminal == "kitty":
        return ["kitty", "bash", path]

    # terminator / tilix / lxterminal / mate-terminal: -e "명령 문자열"
    return [terminal, "-e", f"bash {path}"]


# ─── 계정 스크립트 생성 (tmux / no-tmux 공용) ───────────────────────────────

def create_acct_scripts(group, extra_flags):
    """계정별 /tmp/tennis_acct_N.sh 를 생성하고 경로 목록을 반환한다.

    python 절대 경로를 하드코딩하므로 제한된 PATH 환경에서도 동작한다.
    """
    py = sys.executable
    flags_str = " ".join(extra_flags)
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
    return acct_paths


# ─── tmux 모드: 그룹 스크립트 생성 ──────────────────────────────────────────

def create_group_scripts(group, session_name, extra_flags, group_idx):
    """tmux 세션 생성 + pane 분할 + attach 를 담은 그룹 스크립트를 /tmp에 생성.

    Returns: Path — /tmp/tennis_group_{idx}.sh
    """
    acct_paths = create_acct_scripts(group, extra_flags)
    n = len(group)
    user_ids = ", ".join(a["user_id"] for a in group)

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


# ─── macOS no-tmux: AppleScript 생성 ─────────────────────────────────────────

def build_iterm2_split_applescript(acct_paths):
    """iTerm2 네이티브 split pane AppleScript를 생성한다 (macOS 전용).

    레이아웃:
      1개: [s1          ]
      2개: [s1    | s2  ]
      3개: [s1    | s2  ] / [s3          ]
      4개: [s1    | s2  ] / [s3    | s4  ]

    split 방향:
      vertically   = 수직 divider → s1 오른쪽에 s2 생성
      horizontally = 수평 divider → s1/s2 아래에 s3/s4 생성
    """
    n = len(acct_paths)
    p = [str(path) for path in acct_paths]

    lines = [
        'tell application "iTerm2"',
        '    activate',
        '    set w to (create window with default profile)',
        '    set s1 to current session of w',
        f'    tell s1 to write text "{p[0]}"',
    ]

    if n >= 2:
        lines += [
            '    -- s2: s1 오른쪽 (수직 divider)',
            '    tell s1',
            '        set s2 to (split vertically with default profile)',
            '    end tell',
            f'    tell s2 to write text "{p[1]}"',
        ]

    if n >= 3:
        lines += [
            '    -- s3: s1 아래 (수평 divider)',
            '    tell s1',
            '        set s3 to (split horizontally with default profile)',
            '    end tell',
            f'    tell s3 to write text "{p[2]}"',
        ]

    if n == 4:
        lines += [
            '    -- s4: s2 아래 (수평 divider)',
            '    tell s2',
            '        set s4 to (split horizontally with default profile)',
            '    end tell',
            f'    tell s4 to write text "{p[3]}"',
        ]

    lines += [
        '    tell s1 to select',
        'end tell',
    ]
    return "\n".join(lines)


def build_terminal_tabs_applescript(acct_paths):
    """Terminal.app에서 같은 창에 탭을 추가하는 AppleScript를 생성한다 (macOS 전용)."""
    lines = [
        'tell application "Terminal"',
        '    activate',
        f'    do script "bash {acct_paths[0]}"',
    ]
    for path in acct_paths[1:]:
        lines += [
            '    delay 0.3',
            f'    do script "bash {path}" in front window',
        ]
    lines.append('end tell')
    return "\n".join(lines)


def run_osascript(applescript, dry_run=False, label="osascript"):
    """macOS: AppleScript 실행 또는 dry-run 출력."""
    if dry_run:
        print(f"  [{label}]")
        for line in applescript.splitlines():
            print(f"       {line}")
        print()
        return
    subprocess.run(["osascript", "-e", applescript], check=True)


# ─── 터미널 창 열기 (플랫폼 공용) ────────────────────────────────────────────

def tmux_available():
    try:
        subprocess.run([TMUX_BIN, "-V"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def open_new_terminal(script_path, terminal_app, dry_run=False):
    """새 터미널 창에서 스크립트를 실행한다 (tmux 그룹 스크립트용).

    macOS : AppleScript (iTerm2 / Terminal.app)
    Linux : 감지된 터미널 에뮬레이터로 subprocess.Popen
    """
    if IS_MACOS:
        path_str = str(script_path)
        if terminal_app == "iterm2":
            applescript = (
                'tell application "iTerm2"\n'
                f'    create window with default profile command "bash {path_str}"\n'
                'end tell'
            )
        else:
            applescript = (
                'tell application "Terminal"\n'
                f'    do script "bash {path_str}"\n'
                '    activate\n'
                'end tell'
            )
        run_osascript(applescript, dry_run, label="osascript (tmux)")

    else:
        # Linux
        if not terminal_app:
            print(f"  [WARN] 터미널 에뮬레이터 없음 — 백그라운드로 실행: {script_path.name}")
            if not dry_run:
                log = SCRIPT_DIR / f"{script_path.stem}.log"
                with open(log, "w") as lf:
                    subprocess.Popen(["bash", str(script_path)],
                                     stdout=lf, stderr=subprocess.STDOUT)
            return

        cmd = build_linux_open_cmd(terminal_app, script_path)
        if dry_run:
            print(f"  [Linux {terminal_app}] {' '.join(cmd)}")
        else:
            subprocess.Popen(cmd)


# ─── 실행 모드 1: tmux ───────────────────────────────────────────────────────

def run_multi_terminal(accounts, extra_flags, group_size, dry_run=False):
    """tmux 세션 + 새 터미널 창으로 계정을 분할 실행한다.

    macOS / Linux 모두 동작한다.
    """
    groups = chunk_accounts(accounts, group_size)
    terminal_app = detect_terminal_app()
    total = len(groups)

    print(f"[launch] {len(accounts)}개 계정 → {total}개 터미널 창 "
          f"(창당 최대 {group_size}개 pane)")
    print(f"[launch] 모드: tmux  |  터미널 앱: {terminal_app or '없음 (백그라운드 fallback)'}")
    print()

    for i, group in enumerate(groups, 1):
        session = f"{TMUX_SESSION_PREFIX}_{i}"
        user_ids = [a["user_id"] for a in group]
        print(f"  ── 그룹 {i}/{total}  세션={session}  "
              f"계정={', '.join(user_ids)}")

        if not dry_run:
            subprocess.run(
                [TMUX_BIN, "kill-session", "-t", session], capture_output=True
            )

        group_script = create_group_scripts(group, session, extra_flags, i)

        if dry_run:
            separator = "     " + "─" * 50
            print(f"     그룹 스크립트: {group_script}")
            print()
            print(separator)
            for line in group_script.read_text().splitlines():
                print(f"     {line}")
            print(separator)
            open_new_terminal(group_script, terminal_app, dry_run=True)
            print()
            continue

        open_new_terminal(group_script, terminal_app, dry_run=False)
        if i < total:
            time.sleep(0.5)

    if not dry_run:
        print()
        print(f"[launch] {total}개 터미널 창 생성 완료.")
        sessions = [f"{TMUX_SESSION_PREFIX}_{i}" for i in range(1, total + 1)]
        print(f"         세션 목록: {', '.join(sessions)}")
        print(f"         재접속:    {TMUX_BIN} attach-session -t {TMUX_SESSION_PREFIX}_1")


# ─── 실행 모드 2: no-tmux ─────────────────────────────────────────────────────

def run_without_tmux(accounts, extra_flags, group_size, dry_run=False):
    """--no-tmux: 터미널 앱의 네이티브 분할 / 개별 창으로 실행한다.

    macOS (iTerm2)   : AppleScript split pane → 2×2 분할 창
    macOS (Terminal) : AppleScript 탭 → 같은 창에 탭
    Linux            : 계정마다 개별 터미널 창 (분할 미지원)
    둘 다 없음       : run_background_fallback() 으로 자동 전환
    """
    terminal_app = detect_terminal_app()

    if IS_MACOS:
        _run_no_tmux_macos(accounts, extra_flags, group_size, terminal_app, dry_run)
    else:
        _run_no_tmux_linux(accounts, extra_flags, terminal_app, dry_run)


def _run_no_tmux_macos(accounts, extra_flags, group_size, terminal_app, dry_run):
    """macOS: iTerm2 split pane 또는 Terminal.app 탭."""
    groups = chunk_accounts(accounts, group_size)
    total = len(groups)

    if terminal_app == "iterm2":
        mode_label = "iTerm2 네이티브 split pane"
    else:
        mode_label = "Terminal.app 탭"

    print(f"[launch] {len(accounts)}개 계정 → {total}개 터미널 창 "
          f"(창당 최대 {group_size}개 pane)")
    print(f"[launch] 모드: no-tmux ({mode_label})")
    print()

    for i, group in enumerate(groups, 1):
        user_ids = [a["user_id"] for a in group]
        print(f"  ── 그룹 {i}/{total}  계정={', '.join(user_ids)}")

        acct_paths = create_acct_scripts(group, extra_flags)

        if terminal_app == "iterm2":
            applescript = build_iterm2_split_applescript(acct_paths)
            label = f"iTerm2 split (그룹 {i})"
        else:
            applescript = build_terminal_tabs_applescript(acct_paths)
            label = f"Terminal.app 탭 (그룹 {i})"

        if dry_run:
            separator = "     " + "─" * 50
            print()
            print(separator)
            for line in applescript.splitlines():
                print(f"     {line}")
            print(separator)
            print()
            continue

        run_osascript(applescript, dry_run=False, label=label)
        if i < total:
            time.sleep(0.5)

    if not dry_run:
        print()
        print(f"[launch] {total}개 터미널 창 생성 완료 ({mode_label})")


def _run_no_tmux_linux(accounts, extra_flags, terminal_app, dry_run):
    """Linux: 계정마다 개별 터미널 창을 연다.

    Linux 터미널 에뮬레이터는 AppleScript 같은 원격 분할 API가 없으므로
    계정 한 개당 터미널 창 한 개를 생성한다. 모든 창이 동시에 실행된다.
    """
    if not terminal_app:
        print("[INFO] 터미널 에뮬레이터를 찾을 수 없음 → 백그라운드 subprocess로 전환")
        run_background_fallback(accounts, extra_flags)
        return

    total = len(accounts)
    print(f"[launch] {total}개 계정 → {total}개 터미널 창 (창당 1개)")
    print(f"[launch] 모드: no-tmux (Linux {terminal_app}, 계정당 개별 창)")
    print()

    for i, acct in enumerate(accounts, 1):
        # 계정 스크립트는 그룹이 아닌 단일 계정으로 생성
        acct_paths = create_acct_scripts([acct], extra_flags)
        cmd = build_linux_open_cmd(terminal_app, acct_paths[0])

        print(f"  [{i}/{total}] 계정 {acct['num']} ({acct['user_id']}): "
              f"{' '.join(cmd)}")

        if not dry_run:
            subprocess.Popen(cmd)
            if i < total:
                time.sleep(0.2)

    if not dry_run:
        print()
        print(f"[launch] {total}개 터미널 창 생성 완료.")


# ─── 실행 모드 3: background ─────────────────────────────────────────────────

def run_background_fallback(accounts, extra_flags):
    """--background: 터미널 창 없이 백그라운드 subprocess + 로그 파일로 실행."""
    print(f"[launch] {len(accounts)}개 계정을 백그라운드로 실행합니다.")
    procs = []
    for a in accounts:
        cmd = [sys.executable, str(MAIN_PY), "--account", str(a["num"])] + extra_flags
        log_path = SCRIPT_DIR / f"account_{a['num']}.log"
        with open(log_path, "w") as log_f:
            proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)
        procs.append((a, proc, log_path))
        print(f"  계정 {a['num']:2d} ({a['user_id']}): PID {proc.pid} → {log_path.name}")

    print()
    print("[launch] 모든 프로세스 시작 완료. Ctrl+C 로 전체 종료.")
    print()

    try:
        for a, proc, _ in procs:
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
        description="다중 계정 런처 (macOS / Linux 공용)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
실행 모드:
  (없음)        tmux 세션 + 새 터미널 창  [기본]
  --no-tmux     터미널 네이티브 분할
                  macOS/iTerm2  : 2×2 split pane
                  macOS/Terminal: 탭
                  Linux         : 계정당 개별 창
  --background  백그라운드 subprocess + 로그 파일

.env 설정 예시:
  TENNIS_ACCOUNT_1_ID=user1
  TENNIS_ACCOUNT_1_PW=pass1
  TENNIS_ACCOUNT_1_RESERVATION_1=2026-06-07:10:1
        """,
    )
    parser.add_argument("--test", action="store_true",
                        help="테스트 모드 (대관신청 전 중단)")
    parser.add_argument("--check", action="store_true",
                        help="로그인 테스트만 실행")
    parser.add_argument("--dry-run", action="store_true",
                        help="생성될 명령/스크립트 내용 출력 (창 미생성)")
    parser.add_argument("--no-tmux", action="store_true",
                        help="터미널 네이티브 분할로 실행 (tmux 없이)")
    parser.add_argument("--background", action="store_true",
                        help="백그라운드 subprocess + 로그 파일로 실행")
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
    print(f"  플랫폼: {'macOS' if IS_MACOS else sys.platform}")
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

    # 실행 모드 결정 (우선순위: --background > --no-tmux > tmux > no-tmux fallback)
    if args.background:
        if args.dry_run:
            print("[dry-run] 실행될 명령:")
            for a in accounts:
                flags = " ".join(extra_flags)
                print(f"  python3 {MAIN_PY} --account {a['num']} {flags}")
        else:
            run_background_fallback(accounts, extra_flags)

    elif args.no_tmux:
        run_without_tmux(accounts, extra_flags,
                         group_size=args.group_size, dry_run=args.dry_run)

    elif tmux_available():
        run_multi_terminal(accounts, extra_flags,
                           group_size=args.group_size, dry_run=args.dry_run)

    else:
        print("[INFO] tmux를 찾을 수 없어 --no-tmux 모드로 전환합니다.")
        print()
        run_without_tmux(accounts, extra_flags,
                         group_size=args.group_size, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
