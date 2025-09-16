import streamlit as st
from datetime import datetime
import re
import base64
import os
import pandas as pd
from io import StringIO

# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="DB생명 당월 수수료 계산기", layout="centered")
st.markdown(
    """
    <style>
    .block-container { max-width: 1300px; padding-left: 2rem; padding-right: 2rem; }
    label.css-16idsys, label.css-1p3cay5 { white-space: nowrap; }
    </style>
    """,
    unsafe_allow_html=True
)

def render_title_with_logo_right(logo_path: str, title_text: str, logo_width: int = 100):
    try:
        if not os.path.exists(logo_path):
            raise FileNotFoundError(logo_path)
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; border-bottom:1px solid #ddd; padding-bottom:4px;">
                <h1 style="margin:0; font-size:2.5rem;">📊 {title_text}</h1>
                <img src="data:image/png;base64,{b64}" width="{logo_width}" alt="DB생명 로고" />
            </div>
            """,
            unsafe_allow_html=True
        )
    except Exception:
        st.title(f"📊 {title_text}")

render_title_with_logo_right("DB_logo.png", "당월 수수료 계산기", 120)

def SP(px: int = 16):
    st.markdown(f"<div style='height:{px}px'></div>", unsafe_allow_html=True)

SP(25)

# =========================
# 세션 상태
# =========================
if "entries" not in st.session_state:
    st.session_state.entries = []
if "entry_seq" not in st.session_state:
    st.session_state.entry_seq = 0
if "product_selector" not in st.session_state:
    st.session_state.product_selector = "— 상품을 선택하세요 —"

# =========================
# 유틸: 통화 입력(3자리 콤마)
# =========================
def _format_currency(text_key: str):
    raw = st.session_state.get(text_key, "")
    digits = re.sub(r"[^0-9]", "", raw or "")
    num = int(digits) if digits else 0
    st.session_state[text_key] = f"{num:,}" if num else ""

def currency_input(label: str, key: str, default: int = 0, label_visibility: str = "visible") -> int:
    text_key = f"{key}_text"
    if text_key not in st.session_state:
        st.session_state[text_key] = f"{default:,}" if isinstance(default, int) and default else ""
    st.text_input(label, key=text_key, on_change=_format_currency, args=(text_key,), label_visibility=label_visibility)
    digits = re.sub(r"[^0-9]", "", st.session_state.get(text_key, ""))
    return int(digits) if digits else 0

# =========================
# 기본 정보 입력
# =========================
st.subheader("📝 기본 정보 입력")
SP(25)

st.markdown("<div style='font-size:1.08rem; font-weight:700;'>✔️위임년월 입력</div>", unsafe_allow_html=True)
SP(12)

years = list(range(2025, 1988, -1))  # 2025 ~ 1989
c_year, c_gap, c_month, c_fill = st.columns([0.22, 0.02, 0.18, 0.58])
with c_year:
    y_col, _ = st.columns([0.45, 0.55])
    with y_col:
        year = st.selectbox("위임년도", options=years, index=0, key="year_select")
with c_gap: st.write("")
with c_month:
    m_col, _ = st.columns([0.45, 0.55])
    with m_col:
        month = st.selectbox("위임월", options=list(range(1, 13)), index=7, key="month_select")
with c_fill: st.write("")

st.markdown("""
<style>
div[data-testid="stSelectbox"]:has(#year_select) { width: 120px !important; }
div[data-testid="stSelectbox"]:has(#month_select) { width: 90px !important; }
</style>
""", unsafe_allow_html=True)

SP(20)
st.markdown("<div style='font-size:1.08rem; font-weight:700;'>✔️표준활동 입력</div>", unsafe_allow_html=True)
SP(8)
std_activity = st.checkbox("당월 표준활동 달성 여부", value=False)

SP(20)
st.markdown("<div style='font-size:1.08rem; font-weight:700;'>✔️유지율 입력</div>", unsafe_allow_html=True)
SP(8)

today = datetime.today()
contract_months_now = (today.year - year) * 12 + (today.month - month) + 1  # 1=1차월 ...

def _std_retention(month_idx: int):
    if month_idx <= 2:  return None
    elif month_idx <= 6:  return 93
    elif month_idx <= 12: return 90
    else:                 return 85

_std_now_dynamic = _std_retention(contract_months_now)
_std_13 = _std_retention(13)
_std_25 = _std_retention(25)

if "_ret_anchor" not in st.session_state:
    st.session_state._ret_anchor = (year, month)
if st.session_state._ret_anchor != (year, month):
    st.session_state["retention_1st_val"] = 0 if _std_now_dynamic is None else _std_now_dynamic
    st.session_state["retention_13th_val"] = _std_13 if _std_13 is not None else 85
    st.session_state["retention_25th_val"] = _std_25 if _std_25 is not None else 85
    st.session_state._ret_anchor = (year, month)

if "retention_1st_val" not in st.session_state:
    st.session_state["retention_1st_val"] = 0 if _std_now_dynamic is None else _std_now_dynamic
if "retention_13th_val" not in st.session_state:
    st.session_state["retention_13th_val"] = _std_13 if _std_13 is not None else 85
if "retention_25th_val" not in st.session_state:
    st.session_state["retention_25th_val"] = _std_25 if _std_25 is not None else 85

ret1, ret13, ret25 = st.columns(3)
with ret1:
    retention_1st = st.slider("당월 유지율 (%)", min_value=0, max_value=100, key="retention_1st_val")
    st.markdown(f"<div style='font-size:0.8rem; font-weight:400; color:#f70a12;'>기준 유지율: {'해당사항없음' if _std_now_dynamic is None else str(_std_now_dynamic)+'%'}</div>", unsafe_allow_html=True)
with ret13:
    retention_13th = st.slider("13회차 납입 시점 예상 유지율 (%)", min_value=50, max_value=100, key="retention_13th_val")
    st.markdown(f"<div style='font-size:0.8rem; font-weight:400; color:#f70a12;'>기준 유지율: {'해당사항없음' if _std_13 is None else str(_std_13)+'%'}</div>", unsafe_allow_html=True)
with ret25:
    retention_25th = st.slider("25회차 납입 시점 예상 유지율 (%)", min_value=50, max_value=100, key="retention_25th_val")
    st.markdown(f"<div style='font-size:0.8rem; font-weight:400; color:#f70a12;'>기준 유지율: {'해당사항없음' if _std_25 is None else str(_std_25)+'%'}</div>", unsafe_allow_html=True)

# ▶ 유효환산/정착보장 관련 추가 입력
SP(40)
st.markdown("<div style='font-size:1.08rem; font-weight:700;'>✔️유효환산/정착보장 산출 제반사항 입력</div>", unsafe_allow_html=True)
SP(10)
cA, cB, cC = st.columns([1, 1, 1])
with cA:
    refund_p = currency_input("당월 예상 환수성적 (* 청철/반송/무효/해지)", key="refund_p", default=0)
with cB:
    refund_amt = currency_input("당월 예상 환수금 (* 모집+성과1+초기2 환수금)", key="refund_amt", default=0)
with cC:
    direct_recruits = st.number_input("당월 직도입 인원(명)", min_value=0, max_value=99, value=0, step=1)

st.markdown("---")

# =========================
# [변경] 백엔드에서 마스터 로드 (업로드/미리보기 제거)
# =========================
MASTER_CSV_PATH = "./data/product_master.csv"

@st.cache_data(show_spinner=False)
def load_products_tree_from_csv(path: str):
    if not os.path.exists(path):
        return None, None, None  # TREE, DF, STRATEGIC
    # 인코딩 가변 처리
    with open(path, "rb") as f:
        data_bytes = f.read()
    try:
        raw = data_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        raw = data_bytes.decode("cp949")

    df = pd.read_csv(StringIO(raw))
    # 컬럼 정규화
    def _norm(c: str) -> str:
        k = c.strip().lower().replace(" ", "")
        mapping = {
            "상품명": ["상품명", "product", "상품"],
            "유형": ["유형", "type", "상품유형"],
            "납기": ["납기", "납입", "납입년도", "payyears", "납입년수"],
            "1차년성적률": ["1차년성적률", "성적률1", "rate1", "yr1", "y1"],
            "2차년성적률": ["2차년성적률", "성적률2", "rate2", "yr2", "y2"],
            "3차년성적률": ["3차년성적률", "성적률3", "rate3", "yr3", "y3"],
            "전략건강여부": ["전략건강여부", "전략건강", "strategic", "strategic_health", "sh"],
        }
        for std, alts in mapping.items():
            if k in [a.lower().replace(" ", "") for a in alts]:
                return std
        return c
    df = df.rename(columns={c: _norm(c) for c in df.columns})

    req = {"상품명", "유형", "납기", "1차년성적률", "2차년성적률", "3차년성적률", "전략건강여부"}
    if not req.issubset(set(df.columns)):
        return None, None, None

    # 정제
    df["상품명"] = df["상품명"].astype(str).str.strip()
    df["유형"] = df["유형"].astype(str).str.strip()
    df["납기"] = df["납기"].astype(str).str.strip()
    for col in ["1차년성적률", "2차년성적률", "3차년성적률"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float)
    df["전략건강여부"] = df["전략건강여부"].astype(str).str.upper().str.strip()

    PRODUCTS_TREE = {}
    STRATEGIC_HEALTH = set()

    for _, row in df.iterrows():
        name = row["상품명"]
        tpe  = row["유형"]
        r1, r2, r3 = float(row["1차년성적률"]), float(row["2차년성적률"]), float(row["3차년성적률"])
        pay_list = [x for x in re.split(r"[,\s/]+", row["납기"]) if x] or ["기타"]

        if name not in PRODUCTS_TREE:
            PRODUCTS_TREE[name] = {}
        if tpe not in PRODUCTS_TREE[name]:
            PRODUCTS_TREE[name][tpe] = {"payyears": [], "rates": {}, "strategic": False}

        for py in pay_list:
            if py not in PRODUCTS_TREE[name][tpe]["payyears"]:
                PRODUCTS_TREE[name][tpe]["payyears"].append(py)
            PRODUCTS_TREE[name][tpe]["rates"][py] = (r1, r2, r3)

        if row["전략건강여부"] in ["Y", "YES", "1", "TRUE"]:
            PRODUCTS_TREE[name][tpe]["strategic"] = True
            STRATEGIC_HEALTH.add(name)

    for nm in PRODUCTS_TREE:
        for tp in PRODUCTS_TREE[nm]:
            PRODUCTS_TREE[nm][tp]["payyears"].sort(key=lambda s: (len(s), s))

    return PRODUCTS_TREE, df, STRATEGIC_HEALTH

PRODUCTS_TREE, master_df, STRATEGIC_HEALTH = load_products_tree_from_csv(MASTER_CSV_PATH)
if not PRODUCTS_TREE:
    st.error("상품 마스터를 찾을 수 없습니다. 백엔드에 product_master.csv를 배포해 주세요.")
    st.stop()

# =========================
# [변경] 칼럼 비율 동적 산정 (상품명/유형 폭 확대)
# =========================
def compute_col_weights(tree: dict):
    # 길이에 따라 가변폭 계산 (대략적 문자폭 가중)
    max_name = max((len(nm) for nm in tree.keys()), default=8)
    max_type = max((len(tp) for nm in tree for tp in tree[nm].keys()), default=4)

    name_w = min(6.5, max(4.4, max_name * 0.14))  # 상품명: 더 넓게
    type_w = min(3.8, max(2.4, max_type * 0.12))  # 유형: 넓게
    py_w   = 1.6                                  # 납입년도: 조금 축소
    prem_w = 1.8                                  # 월초 보험료: 조금 축소
    del_w  = 1.0

    return [name_w, type_w, py_w, prem_w, del_w]

# =========================
# 상품 선택 → 자동 추가 (상품명 → 유형 → 납입년도)
# =========================
all_products = ["— 상품을 선택하세요 —"] + sorted(PRODUCTS_TREE.keys())

def on_select_change():
    choice = st.session_state.product_selector
    if choice and choice != all_products[0]:
        st.session_state.entry_seq += 1
        new_id = st.session_state.entry_seq

        types = sorted(PRODUCTS_TREE[choice].keys())
        default_type = types[0] if types else "기타"
        payyears = PRODUCTS_TREE[choice][default_type]["payyears"] if types else ["기타"]
        default_pay = payyears[0] if payyears else "기타"

        st.session_state.entries.append({
            "id": new_id,
            "product": choice,
            "type": default_type,
            "pay_year": default_pay,
            "type_key": f"type_{new_id}",
            "pay_year_key": f"payyear_{new_id}",
            "premium_key": f"premium_{new_id}",
            "premium": 0,
        })
        st.session_state.product_selector = all_products[0]

st.markdown("<div style='font-size:1.08rem; font-weight:700; color:#000000;'>✔️상품 선택</div>", unsafe_allow_html=True)
st.caption("※ 선택 즉시 아래에 계약이 추가됩니다")
st.selectbox("", options=all_products, key="product_selector", on_change=on_select_change)

# =========================
# 등록된 계약 렌더링 (상품명 → 유형 → 납입년도) — 가변 칼럼 폭 적용
# =========================
SP(10)
st.subheader("🧾 상품 목록")

col_weights = compute_col_weights(PRODUCTS_TREE)

if not st.session_state.entries:
    st.info("상품을 선택하면 아래에 계약이 추가됩니다. 동일 상품을 여러 건 추가할 수 있습니다.")
else:
    h1, h2, h3, h4, h5 = st.columns(col_weights)
    with h1: st.markdown("**상품명**")
    with h2: st.markdown("**유형**")
    with h3: st.markdown("**납입년도**")
    with h4: st.markdown("**월초 보험료(원)**")
    with h5: st.markdown("**삭제**")

    remove_id = None
    for e in st.session_state.entries:
        c1, c2, c3, c4, c5 = st.columns(col_weights)

        # 상품명
        with c1:
            prod_opts = sorted(PRODUCTS_TREE.keys())
            cur_prod_idx = prod_opts.index(e["product"]) if e["product"] in prod_opts else 0
            new_prod = st.selectbox("상품명", prod_opts, index=cur_prod_idx, key=f"prod_{e['id']}", label_visibility="collapsed")
            if new_prod != e["product"]:
                e["product"] = new_prod
                types = sorted(PRODUCTS_TREE[new_prod].keys())
                e["type"] = types[0]
                e["pay_year"] = PRODUCTS_TREE[new_prod][e["type"]]["payyears"][0]

        # 유형
        with c2:
            types = sorted(PRODUCTS_TREE[e["product"]].keys())
            if e["type"] not in types:
                e["type"] = types[0]
            new_type = st.selectbox("유형", types, index=types.index(e["type"]), key=e["type_key"], label_visibility="collapsed")
            if new_type != e["type"]:
                e["type"] = new_type
                e["pay_year"] = PRODUCTS_TREE[e["product"]][e["type"]]["payyears"][0]

        # 납입년도
        with c3:
            py_opts = PRODUCTS_TREE[e["product"]][e["type"]]["payyears"]
            if e["pay_year"] not in py_opts:
                e["pay_year"] = py_opts[0]
            e["pay_year"] = st.selectbox("납입년도", py_opts, index=py_opts.index(e["pay_year"]), key=e["pay_year_key"], label_visibility="collapsed")

        # 월초 보험료
        with c4:
            e["premium"] = currency_input("월초 보험료(원)", key=e["premium_key"], default=e.get("premium", 0), label_visibility="collapsed")

        with c5:
            if st.button("🗑 삭제", key=f"del_{e['id']}", use_container_width=True):
                remove_id = e["id"]
        st.markdown("")

    if remove_id is not None:
        st.session_state.entries = [x for x in st.session_state.entries if x["id"] != remove_id]

# =========================
# 계산 로직
# =========================
def get_rates(product: str, tpe: str, payyear: str):
    try:
        r1, r2, r3 = PRODUCTS_TREE[product][tpe]["rates"][payyear]
        return float(r1), float(r2), float(r3)
    except Exception:
        return 0.0, 0.0, 0.0

if st.button("📌 계산하기"):
    st.divider()
    summary_placeholder = st.container()

    # 유지율 보정 계수
    def retention_factor(user_rate: int, standard_rate):
        if standard_rate is None:
            return 1.0
        delta = user_rate - standard_rate
        if delta >= 0:   return 1.00
        elif delta > -5: return 0.85
        else:            return 0.70

    # 성과수수료 기준율 테이블
    def performance_rate_by_months(months: int, eff: float) -> float:
        if eff < 700_000:
            return 0.0
        if months <= 12:
            if eff >= 10_000_000: return 0.75
            if eff >= 5_000_000:  return 0.72
            if eff >= 2_000_000:  return 0.70
            if eff >= 1_000_000:  return 0.60
            return 0.35
        elif months <= 24:
            if eff >= 10_000_000: return 0.80
            if eff >= 5_000_000:  return 0.77
            if eff >= 2_000_000:  return 0.75
            if eff >= 1_000_000:  return 0.65
            return 0.40
        elif months <= 36:
            if eff >= 10_000_000: return 0.85
            if eff >= 5_000_000:  return 0.82
            if eff >= 2_000_000:  return 0.80
            if eff >= 1_000_000:  return 0.70
            return 0.45
        else:
            if eff >= 10_000_000: return 0.90
            if eff >= 5_000_000:  return 0.87
            if eff >= 2_000_000:  return 0.85
            if eff >= 1_000_000:  return 0.75
            return 0.50

    # 유효환산P 산정(1차년 환산 합)
    total_converted_raw = 0
    for e in st.session_state.entries:
        r1, r2, r3 = get_rates(e["product"], e["type"], e["pay_year"])
        total_converted_raw += e["premium"] * (r1 / 100.0)

    effective_converted = max(0, total_converted_raw - refund_p)

    today = datetime.today()
    contract_months = (today.year - year) * 12 + (today.month - month) + 1

    base_rate_raw = performance_rate_by_months(contract_months, effective_converted)
    base_rate = base_rate_raw

    # 초기정착2 전제조건
    cond_std = bool(std_activity)
    cond_month = contract_months <= 12
    cond_amt_init2 = effective_converted >= 1_000_000
    eligible_init2 = cond_std and cond_month and cond_amt_init2

    Rmax = 0.75
    delta_R_raw = max(0.0, Rmax - base_rate) if eligible_init2 else 0.0

    _std_now_dynamic_calc = _std_retention(contract_months)
    f1  = retention_factor(retention_1st, _std_now_dynamic_calc)
    f13 = retention_factor(retention_13th, _std_13)
    f25 = retention_factor(retention_25th, _std_25)

    # 전략건강 건수/단가
    def strategic_count(p: int) -> float:
        if p >= 50_000: return 1.0
        if p >= 30_000: return 0.5
        return 0.0

    total_sh_count = 0.0
    for e in st.session_state.entries:
        if e["product"] in STRATEGIC_HEALTH:
            total_sh_count += strategic_count(e["premium"])

    def per_unit_bonus(cnt: float) -> int:
        if cnt >= 5: return 70_000
        if cnt >= 3: return 60_000
        if cnt >= 2: return 55_000
        if cnt >= 1: return 50_000
        return 0

    sh_unit = per_unit_bonus(total_sh_count)

    # 상품별 계산
    results = []
    sum_recruit = sum_perf1 = sum_init2_1 = sum_sh_bonus = 0

    for e in st.session_state.entries:
        prod, tpe, pay_year, premium = e["product"], e["type"], e["pay_year"], e["premium"]
        r1, r2, r3 = get_rates(prod, tpe, pay_year)

        y1 = premium * (r1 / 100.0)
        y2 = premium * (r2 / 100.0)
        y3 = premium * (r3 / 100.0)

        if direct_recruits >= 3:   dr_bonus = 0.15
        elif direct_recruits == 2: dr_bonus = 0.10
        elif direct_recruits == 1: dr_bonus = 0.05
        else:                      dr_bonus = 0.0

        perf1_rate_effective = (base_rate * f1) + (dr_bonus if base_rate > 0 else 0.0)
        perf1 = y1 * perf1_rate_effective
        perf2 = y2 * base_rate * f13
        perf3 = y3 * base_rate * f25

        init2_1 = y1 * (delta_R_raw * f1)
        init2_2 = y2 * (delta_R_raw * f13)
        init2_3 = y3 * (delta_R_raw * f25)

        retention1_amt = y2 / 12
        retention2_amt = y3 / 12

        sh_flag = (prod in STRATEGIC_HEALTH)
        this_count = strategic_count(premium) if sh_flag else 0.0
        sh_bonus = int(this_count * sh_unit) if sh_flag else 0
        sh_tag = " <span style='color:#dc2626'>[전략건강]</span>" if sh_flag else ""

        recruit_fee = y1

        sum_recruit += recruit_fee
        sum_perf1   += perf1
        sum_init2_1 += init2_1
        sum_sh_bonus += sh_bonus

        results.append({
            "prod": prod, "type": tpe, "pay_year": pay_year, "premium": premium,
            "recruit_fee": recruit_fee, "perf1": perf1, "perf2": perf2, "perf3": perf3,
            "init2_1": init2_1, "init2_2": init2_2, "init2_3": init2_3,
            "retention1_amt": retention1_amt, "retention2_amt": retention2_amt,
            "sh_bonus": sh_bonus, "sh_tag": sh_tag,
        })

    # 정착보장 수수료
    def guarantee_amount_base(effP: int) -> int:
        if effP >= 5_000_000: return 5_000_000
        if effP >= 4_000_000: return 4_500_000
        if effP >= 3_000_000: return 4_000_000
        if effP >= 2_500_000: return 3_500_000
        if effP >= 2_000_000: return 3_000_000
        if effP >= 1_500_000: return 2_500_000
        if effP >= 1_000_000: return 1_500_000
        return 0

    base_guarantee = guarantee_amount_base(effective_converted)
    add_guarantee = 1_000_000 if direct_recruits == 1 else (2_000_000 if direct_recruits >= 2 else 0)
    final_guarantee = base_guarantee + add_guarantee

    cond_ret = (_std_now_dynamic is None) or (retention_1st >= _std_now_dynamic)
    eligible_settle = (contract_months <= 12) and std_activity and cond_ret and (final_guarantee > 0)

    base_comp = sum_recruit + sum_perf1 + sum_init2_1
    base_comp_after_refund = max(0, base_comp - refund_amt)

    settle_bonus = (final_guarantee - base_comp_after_refund) if eligible_settle else 0
    if settle_bonus < 0: settle_bonus = 0

    # ── 상단 요약
    with summary_placeholder:
        st.markdown("<div style='font-size:1.8rem; font-weight:700;'>📢당월 수수료 요약</div>", unsafe_allow_html=True)

        info_lines = [
            f"- **당월환산보험료**: {int(total_converted_raw):,}P",
            f"- **당월 예상 환수성적**: {int(refund_p):,}P",
            f"- **유효환산보험료**: {int(effective_converted):,}P",
            f"- **기준 유지율**: {('해당사항없음' if _std_now_dynamic is None else str(_std_now_dynamic)+'%')}",
            f"- **현재 유지율**: {retention_1st}%",
        ]

        perf_rate_has_base = base_rate_raw > 0
        perf_rate_display = base_rate_raw * f1
        perf_rate_pct = int(perf_rate_display * 100)

        perf_caption_parts = []
        if perf_rate_has_base:
            if f1 != 1.0:
                perf_caption_parts.append(f"지급률 {int(base_rate_raw*100)}% × 유지율 가감 {int(f1*100)}%")
            if direct_recruits >= 1 and base_rate_raw > 0:
                dr_txt = "5%p" if direct_recruits == 1 else ("10%p" if direct_recruits == 2 else "15%p")
                if f1 != 1.0:
                    perf_caption_parts.append(f"+ 직도입우대 {dr_txt}")
                else:
                    perf_caption_parts.append(f"지급률 {int(base_rate_raw*100)}% + 직도입우대 {dr_txt}")

        if perf_caption_parts:
            info_lines.append(f"- **성과수수료 지급률**: {perf_rate_pct}%  ( * " + " ".join(perf_caption_parts) + " )")
        else:
            info_lines.append(f"- **성과수수료 지급률**: {perf_rate_pct}%")

        if contract_months <= 12:
            if add_guarantee > 0:
                info_lines.append(f"- **정착보장수수료 보장금액**: {final_guarantee:,.0f}원 (* 직도입 +{add_guarantee//10000:,}만원)")
            else:
                info_lines.append(f"- **정착보장수수료 보장금액**: {final_guarantee:,.0f}원")

        st.info("  \n".join(info_lines))

        if contract_months <= 12 and settle_bonus == 0:
            reasons_settle = []
            if final_guarantee == 0: reasons_settle.append("유효환산 구간 미달")
            if not std_activity: reasons_settle.append("표준활동 미달성")
            if (_std_now_dynamic is not None) and (retention_1st < _std_now_dynamic): reasons_settle.append("당월 유지율 기준 미달")
            if reasons_settle: st.markdown("**＊ 정착보장수수료 미산출 이유:** " + ", ".join(reasons_settle))

        if not eligible_init2:
            reasons_i2 = []
            if not std_activity: reasons_i2.append("표준활동 미달성")
            if not cond_month: reasons_i2.append("위임 13차월 이상")
            if not cond_amt_init2: reasons_i2.append("유효환산 100만원 미만")
            if cond_month and cond_amt_init2 and base_rate_raw >= 0.75 and contract_months <= 12:
                reasons_i2.append("성과수수료 최대 지급률 달성 상태")
            if reasons_i2: st.markdown("**＊ 초기정착수수료2 미산출 이유:** " + ", ".join(reasons_i2))

        # 익월 요약
        st.markdown("<div style='font-size:1.8rem; font-weight:700; margin-top:8px;'>📢익월 예상 수수료</div>", unsafe_allow_html=True)
        lines = [
            f"- **모집수수료** : {sum_recruit:,.0f}원",
            f"- **성과수수료1** : {sum_perf1:,.0f}원",
            f"- **초기정착수수료2-1** : {sum_init2_1:,.0f}원",
            f"- **전략건강 보너스** : {sum_sh_bonus:,.0f}원",
        ]
        if contract_months <= 12:
            lines.append(f"- **정착보장 수수료** : {settle_bonus:,.0f}원")
        next_month_total = sum_recruit + sum_perf1 + sum_init2_1 + sum_sh_bonus + (settle_bonus if contract_months <= 12 else 0)
        lines.append(f"\n**총합 : {next_month_total:,.0f}원**")
        st.warning("\n".join(lines))

        SP(50)

    # ── [변경] 상품별 상세 (차년 성적률 표시는 제거)
    st.subheader("📆 상품별 예상 수수료 계산")
    for r in results:
        st.markdown("---")
        st.markdown(f"### ✅ {r['prod']} ({r['type']}){r['sh_tag']}", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:1.05rem'><b>월초 보험료</b>: {r['premium']:,.0f}원</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:1.05rem'><b>납입년도</b>: {r['pay_year']}</div>", unsafe_allow_html=True)
        SP(10)

        st.markdown("#### 1차년(익월) 수수료")
        st.write(f"- 모집수수료 : {r['recruit_fee']:,.0f}원")
        st.write(f"- 성과수수료1 : {r['perf1']:,.0f}원")
        st.write(f"- 초기정착수수료2-1 : {r['init2_1']:,.0f}원")
        if r['sh_bonus'] > 0:
            st.write(f"- 전략건강 보너스 : {r['sh_bonus']:,.0f}원")

        st.markdown("#### 2차년 수수료")
        st.write(f"- 유지수수료1 (13~24회차 보험료 납입시): {r['retention1_amt']:,.0f}원")
        st.write(f"- 성과수수료2 : {r['perf2']:,.0f}원")
        st.write(f"- 초기정착수수료2-2 : {r['init2_2']:,.0f}원")

        st.markdown("#### 3차년 수수료")
        st.write(f"- 유지수수료2 (25~36회차 보험료 납입시): {r['retention2_amt']:,.0f}원")
        st.write(f"- 성과수수료3 : {r['perf3']:,.0f}원")
        st.write(f"- 초기정착수수료2-3 : {r['init2_3']:,.0f}원")

        SP(40)

        st.success("**✔️지급조건**\n\n**＊ 성과수수료 : 지급월 기준 환산가동인 자**\n\n**＊ 초기정착수수료2 : 지급월 기준 표준활동 달성 및 유효환산 100만P 이상인 자**")
