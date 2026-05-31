#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테니스장 예약 현황 뷰어

.env의 다중 계정 예약 정보를 달력 형태로 브라우저에 표시한다.
  - 달력 그리드: 날짜 셀마다 코트(1-4) × 시간 미니 그리드
  - 왼쪽 패널: 계정 체크박스, PW 마스킹, 예약 건수
  - 중복 슬롯: 황색 + ⚠ 표시 + 툴팁

사용법:
    python3 viewer.py
    python3 viewer.py 2026 7   # 특정 월 지정
"""

import json
import sys
import webbrowser
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()

ACCOUNT_COLORS = [
    '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
    '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16',
    '#06B6D4', '#D946EF', '#78716C',
]

ALL_COURTS = [1, 2, 3, 4]


# ─── 데이터 로드 ──────────────────────────────────────────────────────────────

def load_data():
    """config 모듈에서 계정과 예약 데이터를 로드한다."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "config", SCRIPT_DIR / "config.py"
    )
    cfg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cfg)
    cfg.load_env_file()

    accounts = []
    for a in cfg.load_accounts():
        res_cfg = a.get("reservation_config") or {}
        reservations = sorted(
            [
                {"date": r["date"], "hour": r["hour"], "court": r["court"]}
                for r in res_cfg.get("reservations", [])
            ],
            key=lambda r: (r["date"], r["hour"], r["court"]),
        )
        accounts.append({
            "num":          a["num"],
            "user_id":      a["user_id"],
            "user_pw":      a.get("user_pw", ""),
            "color":        ACCOUNT_COLORS[(a["num"] - 1) % len(ACCOUNT_COLORS)],
            "reservations": reservations,
        })
    return accounts


def get_initial_month(accounts):
    """예약 데이터 중 가장 빠른 연월을 반환한다."""
    dates = [r["date"] for a in accounts for r in a["reservations"]]
    if dates:
        d = sorted(dates)[0]
        return int(d[:4]), int(d[5:7])
    from datetime import datetime
    n = datetime.now()
    return n.year, n.month


# ─── HTML 생성 ────────────────────────────────────────────────────────────────

_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f1f5f9;color:#1e293b;font-size:14px}

/* 전체 레이아웃 */
.app{display:flex;flex-direction:column;height:100vh;overflow:hidden}
.app-header{display:flex;align-items:center;justify-content:space-between;padding:10px 18px;background:#0f172a;color:#fff;flex-shrink:0}
.app-header h1{font-size:16px;font-weight:700;display:flex;align-items:center;gap:8px}
.header-btns{display:flex;gap:6px}
.header-btns button{padding:5px 12px;border:1px solid rgba(255,255,255,.25);border-radius:6px;background:transparent;color:#fff;cursor:pointer;font-size:12px;transition:background .15s}
.header-btns button:hover{background:rgba(255,255,255,.12)}
.layout{display:flex;flex:1;overflow:hidden}

/* 사이드바 */
.sidebar{width:210px;min-width:210px;background:#fff;border-right:1px solid #e2e8f0;overflow-y:auto;padding:10px 8px;display:flex;flex-direction:column;gap:4px}
.sidebar-label{font-size:10px;font-weight:700;color:#94a3b8;letter-spacing:.08em;text-transform:uppercase;padding:4px 4px 2px}
.acct-card{padding:7px 8px;border-radius:8px;border:1.5px solid transparent;transition:all .15s;background:#fafafa}
.acct-card.on{border-color:var(--c);background:color-mix(in srgb,var(--c) 7%,#fff)}
.acct-card.off{opacity:.38}
.acct-r1{display:flex;align-items:center;gap:5px;margin-bottom:3px}
.acct-cb{width:15px;height:15px;cursor:pointer;flex-shrink:0}
.acct-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;background:var(--c)}
.acct-num{font-size:10px;font-weight:700;color:#64748b;min-width:14px}
.acct-id{font-size:12px;font-weight:700;color:#1e293b;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.acct-r2{display:flex;align-items:center;gap:3px;padding-left:20px}
.pw-box{flex:1;border:none;background:#f1f5f9;border-radius:4px;padding:2px 5px;font-size:10px;color:#475569;font-family:monospace;outline:none;cursor:default}
.pw-eye{background:none;border:none;cursor:pointer;font-size:11px;color:#94a3b8;padding:0;line-height:1}
.pw-eye:hover{color:#475569}
.acct-r3{padding-left:20px;margin-top:2px;font-size:10px;color:#94a3b8}

/* 달력 영역 */
.cal-area{flex:1;overflow:auto;padding:14px}
.month-nav{display:flex;align-items:center;gap:12px;margin-bottom:12px}
.month-nav button{width:30px;height:30px;border:1px solid #e2e8f0;border-radius:7px;background:#fff;cursor:pointer;font-size:14px;transition:background .15s}
.month-nav button:hover{background:#f8fafc}
.month-title{font-size:17px;font-weight:700;min-width:110px;text-align:center}

/* 달력 그리드 */
.cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:3px}
.dow-hd{text-align:center;font-size:11px;font-weight:600;color:#64748b;padding:5px 0}
.dow-hd.sat{color:#2563eb}.dow-hd.sun{color:#dc2626}

.day-cell{background:#fff;border:1px solid #e2e8f0;border-radius:8px;min-height:unset;overflow:hidden;transition:box-shadow .15s}
.day-cell:hover{box-shadow:0 2px 8px rgba(0,0,0,.08)}
.day-cell.blank{background:#f8fafc;border-color:#f1f5f9}
.day-cell.is-today{border:2px solid #3b82f6}
.day-cell.is-sat{background:#eff6ff}.day-cell.is-sun{background:#fef2f2}

.day-num{font-size:12px;font-weight:700;padding:4px 7px 2px;display:flex;justify-content:space-between;align-items:center}
.day-num .dow-tag{font-size:9px;font-weight:500;color:#94a3b8}
.day-num.sat-n{color:#2563eb}.day-num.sun-n{color:#dc2626}

/* 미니 그리드 (코트×시간) */
.mini{padding:0 4px 5px;display:grid;gap:1px}
.ct-hd{font-size:8px;font-weight:700;color:#94a3b8;text-align:center;padding-bottom:1px;line-height:1.2}
.t-label{font-size:8px;color:#94a3b8;font-weight:500;text-align:right;padding-right:2px;line-height:1;display:flex;align-items:center;justify-content:flex-end}

/* 슬롯 */
.slot{height:15px;border-radius:3px;display:flex;align-items:center;justify-content:center;font-size:8px;font-weight:800;cursor:pointer;position:relative;transition:opacity .2s,transform .1s;user-select:none}
.slot:hover{transform:scale(1.15);z-index:20}
.slot.empty{background:#f1f5f9;border:1px dashed #cbd5e1;color:#d1d5db}
.slot.booked{color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.35)}
.slot.dup{background:#fef3c7!important;border:1.5px solid #f59e0b!important;color:#92400e;flex-direction:column;font-size:7px;gap:0;line-height:1.1}
.slot.dimmed{opacity:.08!important;pointer-events:none}
.mini.no-res{opacity:.28}
.mini.no-res .slot{cursor:default}
.mini.no-res .slot:hover{transform:none}

/* 툴팁 */
#tip{position:fixed;background:rgba(15,23,42,.93);color:#fff;padding:7px 11px;border-radius:8px;font-size:12px;line-height:1.65;pointer-events:none;z-index:9999;display:none;white-space:nowrap;box-shadow:0 4px 20px rgba(0,0,0,.3);max-width:280px}
#tip.show{display:block}
.tip-head{font-weight:700;margin-bottom:1px}
.tip-dup{display:inline-block;background:#f59e0b;color:#1e293b;border-radius:4px;padding:0 5px;font-size:10px;font-weight:700;margin-bottom:3px}

/* 범례 */
.legend{display:flex;gap:14px;margin-top:10px;align-items:center;font-size:11px;color:#64748b;flex-wrap:wrap}
.leg-item{display:flex;align-items:center;gap:4px}
.leg-box{width:14px;height:14px;border-radius:3px;flex-shrink:0}
.leg-empty{background:#f1f5f9;border:1px dashed #cbd5e1}
.leg-booked{background:#3b82f6}
.leg-dup{background:#fef3c7;border:1.5px solid #f59e0b}
/* ── 포커스 반전 ── */
.acct-card.fc{background:var(--c)!important;border-color:var(--c)!important}
.acct-card.fc .acct-id,.acct-card.fc .acct-num,.acct-card.fc .acct-r3{color:#fff!important}
.acct-card.fc .pw-box{background:rgba(255,255,255,.2);color:#fff}
.slot.hi{outline:2px solid rgba(255,255,255,.9);z-index:5;filter:brightness(1.12)}
.slot.dfm{opacity:.07!important;pointer-events:none}
/* ── 슬롯 체크 ── */
.slot.ckd{box-shadow:0 0 0 2px #22c55e!important;z-index:6}
.slot.ckd::after{content:'✓';position:absolute;top:-6px;right:-4px;font-size:9px;color:#22c55e;font-weight:900;background:#fff;border-radius:50%;line-height:1;padding:0 1px;z-index:7}
/* ── 체크 패널 ── */
.ck-panel{margin-top:10px;padding:10px 12px;background:#fff;border:1px solid #e2e8f0;border-radius:8px}
.ck-panel h3{font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px}
.ck-tags{display:flex;flex-wrap:wrap;gap:4px;min-height:22px}
.ck-tag{background:#f0fdf4;border:1px solid #86efac;border-radius:4px;padding:2px 8px;font-size:11px;color:#166534;cursor:pointer;transition:background .1s}
.ck-tag:hover{background:#dcfce7}
.ck-none{font-size:11px;color:#cbd5e1}
"""

_JS = r"""
/* ── 상태 ── */
let selected = new Set(ACCOUNTS.map(a => a.num));
let CY, CM;
const ALL_HOURS = [6, 8, 10, 12, 14, 16, 18, 20, 22];
let focusedAcct = null;   // 포커스(반전)된 계정 번호
let checkedSlots = new Set(); // 체크된 슬롯 키 "날짜:시간:코트"

/* ── 초기화 ── */
(function init() {
  const dates = ACCOUNTS.flatMap(a => a.reservations.map(r => r.date)).sort();
  if (dates.length) {
    const p = dates[0].split('-');
    CY = +p[0]; CM = +p[1];
  } else {
    const n = new Date(); CY = n.getFullYear(); CM = n.getMonth() + 1;
  }
  buildSidebar();
  buildCalendar();
})();

/* ── 사이드바 ── */
function buildSidebar() {
  const sb = document.getElementById('sb');
  sb.innerHTML = '<div class="sidebar-label">계정 목록</div>' +
    ACCOUNTS.map(a => {
      const on = selected.has(a.num);
      return `
<div class="acct-card ${on?'on':'off'}" style="--c:${a.color}" id="ac${a.num}"
     onclick="if(!event.target.closest('input,button'))focusAcct(${a.num})">
  <div class="acct-r1">
    <input type="checkbox" class="acct-cb" ${on?'checked':''} onchange="toggleAcct(${a.num})" style="accent-color:${a.color}">
    <span class="acct-dot"></span>
    <span class="acct-num">${a.num}</span>
    <span class="acct-id" title="${a.user_id}">${a.user_id}</span>
  </div>
  <div class="acct-r2">
    <input type="password" id="pw${a.num}" value="${a.user_pw}" class="pw-box" readonly>
    <button class="pw-eye" onclick="togglePw(${a.num})" title="비밀번호 보기">👁</button>
  </div>
  <div class="acct-r3">📅 ${a.reservations.length}건</div>
</div>`;
    }).join('');
}

function toggleAcct(num) {
  selected.has(num) ? selected.delete(num) : selected.add(num);
  const card = document.getElementById('ac'+num);
  if (card) { card.classList.toggle('on', selected.has(num)); card.classList.toggle('off', !selected.has(num)); }
  buildCalendar();  // 선택 상태 변경 시 슬롯 맵 재계산 → 중복 판정 갱신
}

function selectAll(v) {
  ACCOUNTS.forEach(a => {
    v ? selected.add(a.num) : selected.delete(a.num);
    const card = document.getElementById('ac'+a.num);
    if (card) { card.classList.toggle('on',v); card.classList.toggle('off',!v); }
    const cb = card && card.querySelector('.acct-cb');
    if (cb) cb.checked = v;
  });
  buildCalendar();  // 선택 상태 변경 시 슬롯 맵 재계산 → 중복 판정 갱신
}

function refreshDim(el) {
  const accts = JSON.parse(el.dataset.a);
  el.classList.toggle('dimmed', accts.length > 0 && !accts.some(n => selected.has(n)));
}

function togglePw(num) {
  const el = document.getElementById('pw'+num);
  if (el) el.type = el.type === 'password' ? 'text' : 'password';
}

/* ── 월 이동 ── */
function changeMonth(d) {
  CM += d;
  if (CM > 12) { CM = 1; CY++; }
  if (CM < 1)  { CM = 12; CY--; }
  buildCalendar();
}

/* ── 슬롯 맵 ── */
function slotMap() {
  const m = {};
  const pfx = `${CY}-${String(CM).padStart(2,'0')}`;
  ACCOUNTS.forEach(a => {
    if (!selected.has(a.num)) return;  // 선택된 계정만 포함
    a.reservations.forEach(r => {
      if (!r.date.startsWith(pfx)) return;
      const day = +r.date.split('-')[2];
      ((m[day] ??= {})[r.hour] ??= {})[r.court] ??= [];
      m[day][r.hour][r.court].push(a.num);
    });
  });
  return m;
}

/* ── 달력 렌더링 ── */
function buildCalendar() {
  document.getElementById('mtitle').textContent = `${CY}년 ${CM}월`;
  const sm = slotMap();
  const today = new Date();
  const todayD = (today.getFullYear()===CY && today.getMonth()+1===CM) ? today.getDate() : -1;

  const firstDow = (new Date(CY, CM-1, 1).getDay() + 6) % 7; // 월=0
  const lastDay  = new Date(CY, CM, 0).getDate();

  const DOW = ['월','화','수','목','금','토','일'];
  let h = '<div class="cal-grid">';
  DOW.forEach((d,i) => h += `<div class="dow-hd ${i===5?'sat':i===6?'sun':''}">${d}</div>`);

  // 앞 빈 셀
  for (let i = 0; i < firstDow; i++) h += '<div class="day-cell blank"></div>';

  for (let day = 1; day <= lastDay; day++) {
    const dow = (firstDow + day - 1) % 7;
    const sat = dow===5, sun = dow===6;
    const cells = sm[day];
    const colCss = `18px repeat(4,1fr)`;
    const pad = String(day).padStart(2,'0');
    const dateStr = `${CY}-${String(CM).padStart(2,'0')}-${pad}`;

    const hasRes = !!cells;
    h += `<div class="day-cell${sat?' is-sat':sun?' is-sun':''}${day===todayD?' is-today':''}">`;
    h += `<div class="day-num${sat?' sat-n':sun?' sun-n':''}">${day}<span class="dow-tag">${DOW[dow]}</span></div>`;

    // 예약 유무와 관계없이 모든 날짜에 미니 그리드 표시
    // 예약 없는 날: no-res 클래스로 흐리게 처리
    h += `<div class="mini${hasRes ? '' : ' no-res'}" style="grid-template-columns:${colCss}">`;
    h += '<div></div>'; // 시간 레이블 자리
    [1,2,3,4].forEach(c => h += `<div class="ct-hd">C${c}</div>`);
    ALL_HOURS.forEach(hr => {
      h += `<div class="t-label">${String(hr).padStart(2,'0')}</div>`;
      [1,2,3,4].forEach(ct => {
        const accts = cells?.[hr]?.[ct] || [];  // cells 없어도 안전
        h += makeSlot(accts, dateStr, hr, ct);
      });
    });
    h += '</div>';
    h += '</div>';
  }

  // 뒷 빈 셀
  const used = firstDow + lastDay;
  const rem = used % 7;
  if (rem) for (let i = 0; i < 7-rem; i++) h += '<div class="day-cell blank"></div>';

  h += '</div>';
  document.getElementById('cal').innerHTML = h;
  bindTips();
  // 체크된 슬롯 클래스 복원 (달력 재렌더링 후)
  checkedSlots.forEach(key => {
    const [d, h2, c] = key.split(':');
    document.querySelectorAll(`.slot[data-d="${d}"][data-h="${h2}"][data-c="${c}"]`)
      .forEach(el => el.classList.add('ckd'));
  });
  refreshFocus();
  renderCheckedPanel();
}

/* ── 포커스(반전) ── */
function focusAcct(num) {
  focusedAcct = (focusedAcct === num) ? null : num;
  ACCOUNTS.forEach(a => {
    const card = document.getElementById('ac'+a.num);
    if (card) card.classList.toggle('fc', focusedAcct === a.num);
  });
  refreshFocus();
  renderCheckedPanel();
}

function refreshFocus() {
  document.querySelectorAll('.slot[data-a]').forEach(el => {
    const accts = JSON.parse(el.dataset.a);
    el.classList.remove('hi', 'dfm');
    if (focusedAcct === null) return;
    if (accts.includes(focusedAcct)) el.classList.add('hi');
    else if (accts.length > 0)       el.classList.add('dfm');
  });
}

/* ── 슬롯 체크 ── */
function clickSlot(el, dateStr, hr, ct) {
  const key = `${dateStr}:${hr}:${ct}`;
  if (checkedSlots.has(key)) {
    checkedSlots.delete(key);
    el.classList.remove('ckd');
  } else {
    checkedSlots.add(key);
    el.classList.add('ckd');
  }
  renderCheckedPanel();
}

function uncheckSlot(key) {
  checkedSlots.delete(key);
  const [d, h, c] = key.split(':');
  document.querySelectorAll(`.slot[data-d="${d}"][data-h="${h}"][data-c="${c}"]`)
    .forEach(el => el.classList.remove('ckd'));
  renderCheckedPanel();
}

function renderCheckedPanel() {
  const panel = document.getElementById('ck-panel');
  if (!panel) return;
  const acctName = focusedAcct !== null
    ? ' — ' + (ACCOUNTS.find(a => a.num === focusedAcct)?.user_id || '')
    : '';
  const sorted = [...checkedSlots].sort();
  const inner = sorted.length === 0
    ? '<span class="ck-none">슬롯을 클릭해 선택하세요</span>'
    : sorted.map(k => {
        const [d, h, c] = k.split(':');
        return `<span class="ck-tag" onclick="uncheckSlot('${k}')">${d} ${String(+h).padStart(2,'0')}:00 C${c} ×</span>`;
      }).join('');
  panel.innerHTML = `<h3>선택 슬롯${acctName}</h3><div class="ck-tags">${inner}</div>`;
}

function makeSlot(accts, dateStr, hr, ct) {
  const ad = JSON.stringify(accts).replace(/'/g, '&#39;');
  const timeStr = `${String(hr).padStart(2,'0')}:00`;
  const oc = `onclick="clickSlot(this,'${dateStr}',${hr},${ct})"`;

  if (!accts.length) {
    return `<div class="slot empty" data-a="[]" data-d="${dateStr}" data-h="${hr}" data-c="${ct}" ${oc}>□</div>`;
  }
  if (accts.length === 1) {
    const a = ACCOUNTS.find(x => x.num === accts[0]);
    const tip = encodeURIComponent(`${a.user_id}\n${dateStr} ${timeStr}\n코트 ${ct}`);
    return `<div class="slot booked" style="background:${a.color}" data-a='${ad}' data-d="${dateStr}" data-h="${hr}" data-c="${ct}" data-tip="${tip}" ${oc}>${a.num}</div>`;
  }
  // 중복
  const lines = accts.map(n => { const a = ACCOUNTS.find(x=>x.num===n); return `${a.num}: ${a.user_id}`; });
  const tip = encodeURIComponent(`⚠ 중복 ${accts.length}건\n${lines.join('\n')}\n${dateStr} ${timeStr} 코트${ct}`);
  const [n1, n2] = accts;
  return `<div class="slot dup" data-a='${ad}' data-d="${dateStr}" data-h="${hr}" data-c="${ct}" data-tip="${tip}" ${oc}><span>${n1}</span><span>⚠${n2}</span></div>`;
}

/* ── 툴팁 ── */
function bindTips() {
  const tip = document.getElementById('tip');
  document.querySelectorAll('.slot[data-tip]').forEach(el => {
    el.addEventListener('mouseenter', e => {
      const lines = decodeURIComponent(el.dataset.tip).split('\n');
      tip.innerHTML = lines.map((l, i) => {
        if (i === 0) return `<div class="tip-head">${l}</div>`;
        if (l.startsWith('⚠')) return `<div><span class="tip-dup">${l}</span></div>`;
        return `<div>${l}</div>`;
      }).join('');
      tip.classList.add('show');
      move(e);
    });
    el.addEventListener('mousemove', move);
    el.addEventListener('mouseleave', () => tip.classList.remove('show'));
  });
  function move(e) {
    tip.style.left = Math.min(e.clientX+14, window.innerWidth-200) + 'px';
    tip.style.top  = Math.min(e.clientY-10, window.innerHeight-120) + 'px';
  }
}
"""


def build_html(accounts, init_year, init_month):
    data_json = json.dumps(accounts, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>테니스장 예약 현황 — {init_year}년 {init_month}월</title>
<style>{_CSS}</style>
</head>
<body>
<div class="app">
  <header class="app-header">
    <h1>🎾 고양시 테니스장 예약 현황</h1>
    <div class="header-btns">
      <button onclick="selectAll(true)">전체 선택</button>
      <button onclick="selectAll(false)">전체 해제</button>
    </div>
  </header>
  <div class="layout">
    <aside class="sidebar" id="sb"></aside>
    <main class="cal-area">
      <div class="month-nav">
        <button onclick="changeMonth(-1)">◀</button>
        <span class="month-title" id="mtitle"></span>
        <button onclick="changeMonth(1)">▶</button>
      </div>
      <div id="cal"></div>
      <div class="legend">
        <span class="leg-item"><span class="leg-box leg-empty"></span>빈 슬롯</span>
        <span class="leg-item"><span class="leg-box leg-booked"></span>단일 예약</span>
        <span class="leg-item"><span class="leg-box leg-dup"></span>⚠ 중복</span>
        <span class="leg-item" style="color:#94a3b8">ID 클릭 → 반전 포커스 &nbsp;|&nbsp; 슬롯 클릭 → 체크</span>
      </div>
      <div id="ck-panel" class="ck-panel">
        <h3>선택 슬롯</h3>
        <div class="ck-tags"><span class="ck-none">슬롯을 클릭해 선택하세요</span></div>
      </div>
    </main>
  </div>
</div>
<div id="tip"></div>
<script>
const ACCOUNTS = {data_json};
{_JS}
</script>
</body>
</html>"""


# ─── 진입점 ───────────────────────────────────────────────────────────────────

def main():
    accounts = load_data()

    if not accounts:
        print("[ERROR] .env에 TENNIS_ACCOUNT_N_* 계정이 없습니다.")
        sys.exit(1)

    if len(sys.argv) == 3:
        try:
            init_year, init_month = int(sys.argv[1]), int(sys.argv[2])
        except ValueError:
            print("사용법: python3 viewer.py [year] [month]")
            sys.exit(1)
    else:
        init_year, init_month = get_initial_month(accounts)

    html = build_html(accounts, init_year, init_month)

    out = Path("/tmp/tennis_viewer.html")
    out.write_text(html, encoding="utf-8")

    total_res = sum(len(a["reservations"]) for a in accounts)
    print(f"[viewer] 계정 {len(accounts)}개 / 예약 총 {total_res}건")
    print(f"[viewer] 초기 표시: {init_year}년 {init_month}월")
    print(f"[viewer] 파일: {out}")
    print(f"[viewer] 브라우저 실행 중...")
    webbrowser.open(f"file://{out}")


if __name__ == "__main__":
    main()
