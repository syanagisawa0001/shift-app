"""
シフト管理アプリ (プレミアムHTMLカレンダー & 提出状況可視化版)
======================================================
"""

import streamlit as st
import streamlit.components.v1 as components
import requests
import json
from datetime import datetime
import time
import calendar

# ─────────────────────────────────────────────
# ページ設定
# ─────────────────────────────────────────────
st.set_page_config(page_title="Shift Master Pro", page_icon="📅", layout="centered")

# カスタムCSS (モダンダークUI & プレミアムデザイン)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    :root {
        --primary-color: #2979FF;
        --success-color: #00C853;
        --error-color: #FF5252;
        --bg-dark: #0F172A;
        --card-bg: rgba(30, 41, 59, 0.7);
        --border-color: rgba(255, 255, 255, 0.1);
        --text-main: #F8FAFC;
        --text-muted: #94A3B8;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        color: var(--text-main);
    }
    
    /* ガラスモーフィズム・カード */
    .card {
        background: var(--card-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: 24px;
        border-radius: 20px;
        border: 1px solid var(--border-color);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        margin-bottom: 24px;
    }
    
    .section-title {
        font-size: 1.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #2979FF, #00D2FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    /* ──── サイドバー ──── */
    section[data-testid="stSidebar"] {
        background-color: #0B0F1A !important;
        border-right: 1px solid var(--border-color);
    }
    
    /* ──── ラジオボタン (Pill Style) ──── */
    div[role="radiogroup"] { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }
    div[role="radiogroup"] label {
        background: rgba(255, 255, 255, 0.05) !important;
        padding: 10px 20px !important;
        border-radius: 12px !important;
        border: 1px solid var(--border-color) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        margin-right: 0 !important;
    }
    div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child { display: none !important; }
    div[role="radiogroup"] label:has(input:checked) {
        background-color: var(--primary-color) !important;
        border-color: var(--primary-color) !important;
        box-shadow: 0 4px 15px rgba(41, 121, 255, 0.4);
        transform: translateY(-2px);
    }
    div[role="radiogroup"] label:has(input:checked) span { color: white !important; font-weight: 700 !important; }

    /* ──── プレミアムHTMLカレンダー ──── */
    .calendar-container {
        background: rgba(15, 23, 42, 0.5);
        padding: 16px;
        border-radius: 16px;
        border: 1px solid var(--border-color);
    }
    .custom-calendar {
        width: 100%;
        border-collapse: separate;
        border-spacing: 6px;
    }
    .custom-calendar th {
        color: var(--text-muted);
        font-weight: 600;
        padding: 8px 0;
        text-align: center;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .cal-cell {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        height: 85px;
        width: 14.28%;
        padding: 10px;
        vertical-align: top;
        position: relative;
        transition: all 0.25s ease;
    }
    .cal-cell:hover:not(.cal-empty) {
        background: rgba(255, 255, 255, 0.07);
        border-color: rgba(255, 255, 255, 0.2);
        transform: scale(1.02);
    }
    .cal-num {
        font-size: 0.95rem;
        font-weight: 700;
        margin-bottom: 6px;
        display: block;
        color: var(--text-main);
    }
    .cal-shift-text {
        font-size: 0.75rem;
        font-weight: 600;
        line-height: 1.3;
        display: inline-block;
        padding: 4px 8px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        color: var(--text-main);
        width: 100%;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    /* ハイライト */
    .cal-filled {
        background: rgba(0, 200, 83, 0.12) !important;
        border: 1px solid rgba(0, 200, 83, 0.4) !important;
    }
    .cal-filled .cal-shift-text {
        background: var(--success-color);
        color: white;
        box-shadow: 0 2px 8px rgba(0, 200, 83, 0.3);
    }
    .cal-filled-ng {
        background: rgba(255, 82, 82, 0.1) !important;
        border: 1px solid rgba(255, 82, 82, 0.3) !important;
    }
    .cal-filled-ng .cal-shift-text {
        background: var(--error-color);
        color: white;
    }
    .cal-filled-ap {
        background: rgba(255, 171, 0, 0.12) !important;
        border: 1px solid rgba(255, 171, 0, 0.4) !important;
    }
    .cal-filled-ap .cal-shift-text {
        background: #ffab00; /* vibrant amber/orange */
        color: white;
        box-shadow: 0 2px 8px rgba(255, 171, 0, 0.3);
    }
    .cal-holiday .cal-num { color: var(--error-color) !important; opacity: 1; }
    .cal-sat .cal-num { color: var(--primary-color) !important; opacity: 1; }
    .cal-empty { background: transparent; border: none; }
    .cal-today { 
        border: 2px solid var(--primary-color) !important;
        box-shadow: inset 0 0 10px rgba(41, 121, 255, 0.2);
    }
    .cal-today::after {
        content: "TODAY";
        position: absolute;
        bottom: 4px;
        right: 8px;
        font-size: 0.55rem;
        font-weight: 800;
        color: var(--primary-color);
    }

    /* ──── 申請フロー ──── */
    .time-picker-box {
        background: rgba(255, 255, 255, 0.03);
        padding: 20px;
        border-radius: 16px;
        border: 1px solid var(--border-color);
        margin: 15px 0;
    }

    .shift-info-row {
        background: rgba(255, 255, 255, 0.02);
        padding: 14px 20px;
        border-radius: 12px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 4px solid var(--border-color);
        transition: all 0.2s;
    }
    .shift-info-row:hover { background: rgba(255, 255, 255, 0.05); }
    .status-pill {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .st-filled { background: var(--success-color); color: white; }
    .st-empty { background: rgba(255, 255, 255, 0.1); color: var(--text-muted); }
    .st-off { background: #FFFFFF; color: #0F172A; }

    /* デザイン調整 */
    hr { border-color: var(--border-color); opacity: 0.5; }
    </style>

""", unsafe_allow_html=True)

# 再描画時にスクロール位置を維持し、意図しない最下部ジャンプを防ぐ
components.html(
    """
    <script>
    const KEY = "shift_app_scroll_y";
    const parentWindow = window.parent;
    const parentDoc = parentWindow.document;

    if (!parentWindow.__shiftScrollBound) {
        const saveScroll = () => {
            const y = parentWindow.scrollY || parentDoc.documentElement.scrollTop || 0;
            parentWindow.sessionStorage.setItem(KEY, String(y));
        };
        parentDoc.addEventListener("scroll", saveScroll, { passive: true });
        parentWindow.addEventListener("beforeunload", saveScroll);
        parentWindow.__shiftScrollBound = true;
    }

    const savedY = parentWindow.sessionStorage.getItem(KEY);
    if (savedY !== null) {
        setTimeout(() => {
            parentWindow.scrollTo(0, parseInt(savedY, 10) || 0);
        }, 0);
    }
    </script>
    """,
    height=0,
)

# ── ヘルパー ──
WEEKDAYS_JP = ["月", "火", "水", "木", "金", "土", "日"]
def get_weekday(date_str):
    try:
        # date_str: "3/1" -> "2026/3/1"
        current_year = datetime.now().year
        d = datetime.strptime(f"{current_year}/{date_str.strip()}", "%Y/%m/%d")
        return f"({WEEKDAYS_JP[d.weekday()]})"
    except: return ""

def call_gas(method="GET", data=None):
    url = st.secrets.get("GAS_WEBAPP_URL")
    if not url:
        st.error("⚠️ secrets.toml に URL がありません")
        st.stop()
    try:
        if method == "GET": 
            res = requests.get(url, params=data, timeout=15)
        else: 
            res = requests.post(url, data=json.dumps(data), timeout=15)
        return res.json()
    except Exception as e:
        st.error(f"📡 通信エラー: {e}")
        return None

@st.cache_data(ttl=60)
def load_data(target_month=None):
    params = {}
    if target_month:
        params["target_month"] = target_month
        
    res = call_gas("GET", params)
    if res and "date_headers" in res:
        return res
    return get_dummy_data()

# ── データ取得 ──
# ログインやサイドバー描画の前に初期データを確保する
if "target_month" not in st.session_state:
    st.session_state["target_month"] = f"{datetime.now().year}-{datetime.now().month:02d}"

if "sheet_info" not in st.session_state:
    with st.spinner("📡 データ同期中..."):
        st.session_state["sheet_info"] = load_data(st.session_state["target_month"])

# ─────────────────────────────────────────────
# サイドバー: Auth
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2 style='letter-spacing:-1px;'>🛡️ Auth</h2>", unsafe_allow_html=True)
    if st.button("🔄 最新の情報に更新"):
        st.session_state.pop("sheet_info", None); st.rerun()
    
    st.divider()
    auth_opt = st.radio("メニュー", ["ログイン", "新規登録"], horizontal=False)

    logged_user = None
    if auth_opt == "ログイン":
        ln = st.text_input("名前", placeholder="例: 山田太郎")
        lp = st.text_input("PIN (4桁)", type="password", placeholder="****")
        if st.button("ログイン 🚀", key="login_btn", use_container_width=True):
            users = st.session_state["sheet_info"].get("users", [])
            found = False
            for u in users:
                if str(u["username"]).strip() == ln.strip() and str(u["pin"]).strip() == lp.strip():
                    st.session_state["current_user"] = ln.strip(); found = True; break
            if found: st.success("ログイン成功"); time.sleep(0.5); st.rerun()
            else: st.error("名前またはPINが違います")
    else:
        nn = st.text_input("フルネーム")
        np = st.text_input("PIN (4桁の数字)", type="password", max_chars=4)
        if st.button("アカウント作成 🆕", use_container_width=True):
            if not nn or not np: st.warning("入力を確認してください")
            else:
                with st.spinner("登録中..."):
                    res = call_gas("POST", {"type": "signup", "username": nn, "pin": np})
                    if res and res.get("success"):
                        st.success("🎉 登録完了！"); st.session_state.pop("sheet_info", None)
                        time.sleep(1.5); st.rerun()
                    else: st.error("登録できませんでした")

    if "current_user" in st.session_state:
        logged_user = st.session_state["current_user"]
        st.divider(); 
        if st.button("🚪 ログアウト", use_container_width=True):
            del st.session_state["current_user"]; st.rerun()

if not logged_user:
    st.title("🌙 Shift Master")
    st.markdown("""
        ### ようこそ！
        サイドバーからログインして、シフトを管理しましょう。
        
        - 📅 カレンダーで提出状況を確認
        - 🚀 一括でシフトを申請
        - 📱 スマホ対応のモダンUI
    """)
    st.stop()

# ─────────────────────────────────────────────
# カスタムカレンダー生成関数
# ─────────────────────────────────────────────
def render_custom_calendar(user_shifts, date_headers):
    # スプレッドシートのデータから表示月を推測
    now = datetime.now()
    month_to_show = now.month
    year_to_show = now.year
    
    if date_headers:
        try:
            # "3/1" などの形式から月を取得
            first_date = date_headers[0]
            month_to_show = int(first_date.split('/')[0])
        except: pass
        
    cal = calendar.monthcalendar(year_to_show, month_to_show)
    
    html = f'''
    <div class="calendar-container">
    <div style="text-align:center; margin-bottom:15px; font-weight:800; color:var(--primary-color); font-size:1.1rem;">
        {year_to_show}年 {month_to_show}月
    </div>
    <table class="custom-calendar">
        <thead><tr><th>月</th><th>火</th><th>水</th><th>木</th><th>金</th><th>土</th><th>日</th></tr></thead>
        <tbody>
    '''
    
    for week in cal:
        html += '<tr>'
        for i, day in enumerate(week):
            if day == 0:
                html += '<td class="cal-cell cal-empty"></td>'
            else:
                # 複数の日付形式を試行 ( "3/1", "03/01", "3/01" 等に対応 )
                date_keys = [f"{month_to_show}/{day}", f"{month_to_show}/{day:02d}", f"{month_to_show:02d}/{day}", f"{month_to_show:02d}/{day:02d}"]
                shift_val = ""
                for k in date_keys:
                    if k in user_shifts:
                        shift_val = user_shifts[k].strip()
                        break
                
                # スタイル判定
                classes = ["cal-cell"]
                if i == 5: classes.append("cal-sat")
                if i == 6: classes.append("cal-holiday")
                if day == now.day and month_to_show == now.month: classes.append("cal-today")
                
                display_shift = ""
                if shift_val and shift_val not in ["", "（未入力）", None]:
                    if shift_val == "×": classes.append("cal-filled-ng")
                    elif shift_val in ["A", "P"]: classes.append("cal-filled")
                    else: classes.append("cal-filled")
                    display_shift = shift_val
                
                class_str = " ".join(classes)
                html += f'<td class="{class_str}">'
                html += f'<span class="cal-num">{day}</span>'
                if display_shift:
                    html += f'<span class="cal-shift-text">{display_shift}</span>'
                html += '</td>'
        html += '</tr>'
    
    html += '</tbody></table>'
    html += '</div>'
    return html

# ─────────────────────────────────────────────
# メイン画面
# ─────────────────────────────────────────────
st.title("🌙 Shift Master")
st.caption(f"ログイン中: **{logged_user}** 様")

# 月選択UI
info = st.session_state["sheet_info"]
available_months = info.get("available_months", [st.session_state["target_month"]])

# 次の月なども選べるように候補を作成 (現在のリストになければ追加)
upcoming_months = []
today = datetime.now()
for i in range(3):
    m = today.month + i
    y = today.year + (m - 1) // 12
    m = (m - 1) % 12 + 1
    upcoming_months.append(f"{y}-{m:02d}")

all_month_options = sorted(list(set(available_months + upcoming_months)), reverse=True)

selected_month = st.selectbox(
    "📅 対象月を選択", 
    all_month_options, 
    index=all_month_options.index(st.session_state["target_month"]) if st.session_state["target_month"] in all_month_options else 0
)

# 月が変更されたらデータを再取得
if selected_month != st.session_state["target_month"]:
    st.session_state["target_month"] = selected_month
    with st.spinner(f"{selected_month} のデータを読み込んでいます..."):
        st.session_state["sheet_info"] = load_data(selected_month)
        st.rerun()

info = st.session_state["sheet_info"]
date_headers = info.get("date_headers", [])
t_opts = [f"{h:02d}:{m:02d}" for h in range(9, 24) for m in [0, 30]]
my_shifts = info.get("all_shift_data", {}).get(logged_user, {})

t1, t2 = st.tabs(["🚀 一括申請", "📅 確認・修正"])

# ── Tab 1: 一括申請 ──
with t1:
    # 1. カレンダー表示
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 提出ステータス</div>', unsafe_allow_html=True)
    st.markdown(render_custom_calendar(my_shifts, date_headers), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. リスト形式の申請フォーム
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">✍️ シフトを申請</div>', unsafe_allow_html=True)
    st.markdown("<p style='color:var(--text-muted); font-size:0.9rem; margin-bottom:20px;'>各日程のシフトを選択してください。変更しない（「未選択」の）日は <strong>自動的に「❌ (休み)」</strong> として送信されます。</p>", unsafe_allow_html=True)

    # 過去に入力した時間を抽出
    past_times_set = set()
    for val in my_shifts.values():
        if val and isinstance(val, str):
            val = val.strip()
            if val not in ["◯", "×", "（未入力）", ""] and "-" in val:
                past_times_set.add(val)
    # 最大5件まで
    past_times_list = sorted(list(past_times_set))[:5] 
    
    # 時間指定時の選択肢リスト (履歴 + 手動)
    time_options = past_times_list + ["🕒 手動で指定"]

    submission_data = {}

    if not date_headers:
        st.info("データがありません。")
    else:
        # 日付ごとに選択行を作成
        for d in date_headers:
            st.markdown(f"<div style='margin-bottom:8px; font-weight:700;'>📅 {d} {get_weekday(d)}</div>", unsafe_allow_html=True)
            
            # 各日付用の選択肢
            sc = st.radio(f"shift_type_{d}", ["未選択 (❌)", "◯ 終日", "A (午前)", "P (午後)", "⏰ 時間"], label_visibility="collapsed", horizontal=True, key=f"bulk_{d}")
            
            if "時間" in sc:
                st.markdown('<div class="time-picker-box" style="margin-top:0; padding:10px 15px;">', unsafe_allow_html=True)
                
                # 履歴または手動の選択肢
                selected_time_opt = st.radio(
                    f"time_val_{d}",
                    time_options,
                    horizontal=True,
                    label_visibility="collapsed",
                    key=f"time_val_sel_{d}"
                )
                
                if selected_time_opt == "🕒 手動で指定":
                    c1, c2 = st.columns(2)
                    st_t = c1.selectbox("開始", t_opts, index=2, key=f"bulk_st_{d}")
                    en_t = c2.selectbox("終了", t_opts, index=12, key=f"bulk_en_{d}")
                    submission_data[d] = f"{st_t}-{en_t}"
                else:
                    submission_data[d] = selected_time_opt
                    
                st.markdown('</div>', unsafe_allow_html=True)
            elif "◯" in sc:
                submission_data[d] = "◯"
            elif "A" in sc:
                submission_data[d] = "A"
            elif "P" in sc:
                submission_data[d] = "P"
            else:
                submission_data[d] = "×" # 未選択の場合など
            
            st.markdown("<hr style='margin:15px 0; opacity:0.3;'>", unsafe_allow_html=True)

    if st.button("この内容で一括送信 🚀", type="primary", use_container_width=True):
        with st.spinner("送信中..."):
            updates = [{"date_label": d, "shift_value": val} for d, val in submission_data.items()]
            payload = {
                "type": "update", 
                "staff_name": logged_user, 
                "updates": updates,
                "target_month": st.session_state["target_month"]
            }
            res = call_gas("POST", payload)
            if res and res.get("success"):
                st.balloons()
                st.success(f"✅ {len(updates)}日分を反映しました！")
                time.sleep(1.5)
                st.session_state.pop("sheet_info", None)
                load_data.clear()
                st.rerun()
            else: st.error("反映できませんでした")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Tab 2: 確認・修正 ──
with t2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🔍 申請済みの詳細</div>', unsafe_allow_html=True)
    
    if not my_shifts:
        st.info("💡 まだ申請データがありません。")
    else:
        # 日付順にソート (可能な場合)
        for d in date_headers:
            val = my_shifts.get(d, "")
            dv = val if val and str(val).strip() else "（未入力）"
            if dv == "×":
                status_class = "st-off"
            elif dv == "（未入力）":
                status_class = "st-empty"
            else:
                status_class = "st-filled"
            
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f'''
                    <div class="shift-info-row">
                        <span style="font-weight:600;">📅 {d} {get_weekday(d)}</span>
                        <span class="status-pill {status_class}">{dv}</span>
                    </div>
                ''', unsafe_allow_html=True)
            with c2:
                with st.popover("🖊️"):
                    st.markdown(f"**{d} の修正**")
                    no = st.radio("希望", ["◯ 終日", "A (午前)", "P (午後)", "× 休み", "⏰ 時間"], key=f"e_{d}")
                    ev = ""
                    if "◯" in no: ev = "◯"
                    elif "A" in no: ev = "A"
                    elif "P" in no: ev = "P"
                    elif "×" in no: ev = "×"
                    else:
                        ec1, ec2 = st.columns(2)
                        sth = ec1.selectbox("開始", t_opts, index=2, key=f"es_{d}")
                        enh = ec2.selectbox("終了", t_opts, index=12, key=f"ee_{d}")
                        ev = f"{sth}-{enh}"
                    if st.button("更新する", key=f"eb_{d}", use_container_width=True):
                        with st.spinner("更新中..."):
                            payload = {
                                "type": "update", 
                                "staff_name": logged_user, 
                                "updates": [{"date_label": d, "shift_value": ev}],
                                "target_month": st.session_state["target_month"]
                            }
                            res = call_gas("POST", payload)
                            if res and res.get("success"):
                                st.success("完了")
                                time.sleep(0.5)
                                st.session_state.pop("sheet_info", None)
                                load_data.clear()
                                st.rerun()
                            else: st.error("失敗しました")
    st.markdown('</div>', unsafe_allow_html=True)
