import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Painel Treeal Alertas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 96rem;
    }

    .main-title {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.15rem;
        letter-spacing: -0.02em;
    }

    .sub-title {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 1rem;
    }

    .section-title {
        font-size: 1.15rem;
        font-weight: 800;
        margin-top: 0.4rem;
        margin-bottom: 0.75rem;
    }

    .filter-wrap {
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 18px;
        padding: 12px 14px;
        background: rgba(15,23,42,0.35);
        margin-bottom: 12px;
    }

    .soft-card {
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 18px;
        padding: 14px 16px;
        background: rgba(15,23,42,0.42);
        margin-bottom: 12px;
    }

    .status-card {
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 18px;
        padding: 14px 16px;
        background: rgba(15,23,42,0.55);
        min-height: 132px;
    }

    .status-title {
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 0.35rem;
    }

    .muted {
        font-size: 0.82rem;
        color: #94a3b8;
    }

    .normal {
        color: #22c55e;
        font-weight: 800;
    }

    .alerta {
        color: #f59e0b;
        font-weight: 800;
    }

    .critico {
        color: #ef4444;
        font-weight: 800;
    }

    .insight-box {
        border-left: 4px solid #3b82f6;
        background: rgba(59,130,246,0.10);
        border-radius: 12px;
        padding: 12px 14px;
        margin: 0.5rem 0 1rem 0;
    }

    .event-box {
        border: 1px solid rgba(148,163,184,0.12);
        border-radius: 14px;
        padding: 10px 12px;
        background: rgba(255,255,255,0.03);
        margin-bottom: 8px;
    }

    .med-item {
        border: 1px solid rgba(148,163,184,0.16);
        border-left: 5px solid #facc15;
        border-radius: 12px;
        padding: 12px 14px;
        background: rgba(255,255,255,0.03);
        margin-bottom: 10px;
    }

    .med-title {
        font-size: 1.05rem;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .chip {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
        margin-right: 6px;
    }

    .chip-red {
        background: rgba(239,68,68,0.16);
        color: #ef4444;
    }

    .chip-yellow {
        background: rgba(245,158,11,0.16);
        color: #f59e0b;
    }

    .chip-green {
        background: rgba(34,197,94,0.16);
        color: #22c55e;
    }

    div[data-baseweb="tab-list"] {
        gap: 0.5rem;
    }

    button[data-baseweb="tab"] {
        border-radius: 999px !important;
        padding: 0.45rem 0.9rem !important;
        border: 1px solid rgba(148,163,184,0.22) !important;
        background: rgba(15,23,42,0.35) !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        background: rgba(59,130,246,0.18) !important;
        border: 1px solid rgba(59,130,246,0.55) !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HELPERS
# ============================================================
def fmt_int(v):
    return f"{int(round(v)):,}".replace(",", ".")

def fmt_money(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_money_mi(v):
    return f"R$ {v:.2f} MM"

def pct_delta(current, reference):
    if reference == 0:
        return 0.0
    return ((current - reference) / reference) * 100

def status_class(status: str) -> str:
    return {
        "Normal": "normal",
        "Atenção": "alerta",
        "Crítico": "critico"
    }[status]

def classify_trans_delta(delta):
    if delta <= -15:
        return "Crítico"
    if delta <= -8:
        return "Atenção"
    if delta >= 18:
        return "Crítico"
    if delta >= 10:
        return "Atenção"
    return "Normal"

def classify_med_delta(delta):
    if delta >= 15:
        return "Crítico"
    if delta >= 8:
        return "Atenção"
    return "Normal"

def classify_valor_delta(delta):
    if delta <= -15:
        return "Crítico"
    if delta <= -8:
        return "Atenção"
    if delta >= 16:
        return "Crítico"
    if delta >= 10:
        return "Atenção"
    return "Normal"

def append_event(message, level="info"):
    if "event_log" not in st.session_state:
        st.session_state.event_log = []
    st.session_state.event_log.insert(0, {
        "hora": datetime.now().strftime("%H:%M:%S"),
        "nivel": level,
        "mensagem": message
    })
    st.session_state.event_log = st.session_state.event_log[:40]

def render_status_card(title, status, text, detail):
    cls = status_class(status)
    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-title">{title}</div>
            <div class="{cls}">{status}</div>
            <div style="margin-top:8px;">{text}</div>
            <div class="muted" style="margin-top:10px;">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_med_case(case):
    tag = case["tag"]
    if tag == "VENCIDO":
        tag_class = "chip-red"
    elif tag == "D0":
        tag_class = "chip-yellow"
    else:
        tag_class = "chip-green"

    st.markdown(
        f"""
        <div class="med-item">
            <div class="med-title">
                <span class="chip {tag_class}">{case["tag"]}</span>
                {case["id"]} - {case["empresa"]}
            </div>
            <div style="margin-bottom:6px;">
                <a href="#" style="color:#60a5fa;text-decoration:none;">Abrir</a>
            </div>
            <div class="muted">
                Criação: {case["criacao"]} | Prazo: {case["prazo"]} | Dias: {case["dias"]} | Valor: {fmt_money(case["valor"])}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def ensure_finance_columns(df: pd.DataFrame) -> pd.DataFrame:
    defaults = {
        "Saldo Total": 11.80,
        "Saldo Bloqueado": 2.20,
        "Saldo PI": 3.24,
        "Saldo Treeal": 1.18,
    }
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default
    return df

# ============================================================
# INIT STATE
# ============================================================
def init_state(force_reset: bool = False):
    if force_reset:
        keys = list(st.session_state.keys())
        for key in keys:
            del st.session_state[key]

    if "initialized" in st.session_state:
        if "financeiro_diario" in st.session_state:
            fin_df = st.session_state.financeiro_diario
            if {"Saldo Total", "Saldo Bloqueado", "Saldo PI", "Saldo Treeal"}.issubset(fin_df.columns):
                return

    now = datetime.now().replace(microsecond=0)
    now = now.replace(second=30 if now.second >= 30 else 0)

    timestamps = [now - timedelta(seconds=30 * (119 - i)) for i in range(120)]

    trans = []
    meds = []
    vals = []

    t = 250
    m = 3.0
    v = 0.105

    for i in range(120):
        t = max(120, t + np.sin(i / 8) * 2 + np.random.normal(0, 4))
        m = max(0.5, m + np.sin(i / 10) * 0.05 + np.random.normal(0, 0.07))
        v = max(0.03, v + np.sin(i / 9) * 0.002 + np.random.normal(0, 0.003))
        trans.append(int(round(t)))
        meds.append(round(m, 2))
        vals.append(round(v, 3))

    st.session_state.intrahora = pd.DataFrame({
        "timestamp": timestamps,
        "transacoes_atual": trans,
        "transacoes_media": [max(100, int(x * np.random.uniform(0.96, 1.04))) for x in trans],
        "med_atual": meds,
        "med_media": [round(max(0.4, x * np.random.uniform(0.94, 1.06)), 2) for x in meds],
        "valor_atual": vals,
        "valor_medio": [round(max(0.03, x * np.random.uniform(0.95, 1.05)), 3) for x in vals],
    })

    days = pd.date_range(end=pd.Timestamp.today().normalize(), periods=10)

    st.session_state.med_diario = pd.DataFrame({
        "Dia": days,
        "MEDs": [380, 402, 395, 430, 460, 475, 490, 505, 520, 548],
        "Tratados": [250, 270, 255, 300, 315, 320, 340, 355, 366, 390],
        "Aguardando": [130, 132, 140, 130, 145, 155, 150, 150, 154, 158]
    })

    st.session_state.financeiro_diario = pd.DataFrame({
        "Dia": days,
        "Saldo Total": [9.8, 10.1, 9.9, 10.3, 10.7, 10.5, 11.1, 10.9, 11.3, 11.8],
        "Saldo Bloqueado": [1.2, 1.1, 1.3, 1.35, 1.5, 1.45, 1.7, 1.8, 1.95, 2.2],
        "Saldo PI": [3.03, 3.05, 3.81, 3.51, 3.28, 2.75, 2.30, 2.40, 2.86, 3.24],
        "Saldo Treeal": [1.15, 1.15, 1.16, 1.16, 1.16, 1.17, 1.17, 1.17, 1.18, 1.18],
    })

    st.session_state.sla_diario = pd.DataFrame({
        "Dia": days,
        "SLA (%)": [97.2, 97.5, 96.8, 96.9, 97.1, 97.0, 96.5, 96.2, 96.8, 97.3],
        "Tempo Médio (min)": [4.8, 4.7, 5.0, 5.2, 4.9, 5.1, 5.4, 5.6, 5.0, 4.6]
    })

    st.session_state.trans_intraday = pd.DataFrame({
        "Hora": list(range(16)),
        "D0": [42.07, 37.12, 15.38, 12.45, 11.20, 17.89, 26.45, 31.12, 36.18, 4.70, 5.20, 6.83, 12.55, 54.09, 53.00, 52.47],
        "D-1": [46.12, 40.35, 26.80, 18.90, 14.10, 17.00, 22.30, 29.00, 31.70, 36.20, 39.10, 41.30, 43.00, 45.10, 49.20, 50.30],
        "D-7": [12.00, 28.50, 24.10, 23.00, 22.50, 21.70, 30.10, 39.50, 42.80, 41.90, 41.00, 40.20, 51.30, 52.70, 78.50, 60.10]
    })

    st.session_state.top_med_names = [
        " OPERACOES E NEGOCIOS", "PHOEN GAMING LTDA", "DIGIMAIS TECNOLOGIA",
        "WITE RECUPERATION", "ALPHA BANK", "MERCURY PAY",
        "NOVA SOLUCAO", "TECH PIX", "CONTA CERTA", "GRUPO ATLAS"
    ]
    st.session_state.top_med_base = [3524, 2716, 731, 222, 17, 11, 5, 5, 4, 1]

    st.session_state.top_fin_names = [
        "Phoen Gaming", " Operações", "Digimais", "Alpha Bank", "Mercury Pay"
    ]
    st.session_state.top_fin_contas = ["11.946", "11.737", "11.552", "11.801", "11.902"]

    st.session_state.top_trx_names = [
        "PHOEN GAMING LTDA", " OPERACOES E NEGOCIOS", "DIGIMAIS TECNOLOGIA",
        "ALPHA BANK", "MERCURY PAY", "NOVA SOLUCAO",
        "TECH PIX", "CONTA CERTA", "GRUPO ATLAS", "PIX HUB"
    ]
    st.session_state.top_trx_base = [399959, 72390, 977, 136, 73, 63, 51, 22, 18, 12]

    st.session_state.filas = {
        "Processando": 182,
        "Pendentes": 41,
        "Falhas": 7,
        "Reprocesso": 13
    }

    st.session_state.med_cases = [
        {"tag": "D+5", "id": 919, "empresa": " OPERACOES E NEGOCIOS", "criacao": "18/03", "prazo": "28/03", "dias": "5D", "valor": 2200.00},
        {"tag": "D+5", "id": 965, "empresa": " OPERACOES E NEGOCIOS", "criacao": "18/03", "prazo": "28/03", "dias": "5D", "valor": 500.00},
        {"tag": "VENCIDO", "id": 881, "empresa": "PHOEN GAMING LTDA", "criacao": "13/03", "prazo": "23/03", "dias": "-1D", "valor": 8450.00},
        {"tag": "D0", "id": 902, "empresa": "DIGIMAIS TECNOLOGIA", "criacao": "14/03", "prazo": "24/03", "dias": "0D", "valor": 1300.00},
    ]

    st.session_state.tick = 0
    st.session_state.initialized = True
    st.session_state.event_log = []
    append_event("Simulação iniciada.", "info")

# ============================================================
# UPDATE SIMULATION
# ============================================================
def update_simulation():
    now = datetime.now().replace(microsecond=0)
    now = now.replace(second=30 if now.second >= 30 else 0)

    df = st.session_state.intrahora
    while df.iloc[-1]["timestamp"] < now:
        last = df.iloc[-1]
        tick = st.session_state.tick

        trans_step = [10, 5, -4, 8, -2, 14, -6, 9][tick % 8]
        med_step = [0.10, 0.05, -0.06, 0.18, -0.03, 0.12, -0.02, 0.07][tick % 8]
        val_step = [0.003, 0.001, -0.002, 0.004, -0.001, 0.003, -0.001, 0.002][tick % 8]

        trans_atual = max(100, int(last["transacoes_atual"] + trans_step + np.random.normal(0, 4)))
        trans_media = max(100, int(last["transacoes_media"] * 0.93 + trans_atual * 0.07 + np.random.normal(0, 3)))

        med_atual = max(0.5, round(last["med_atual"] + med_step + np.random.normal(0, 0.05), 2))
        med_media = max(0.5, round(last["med_media"] * 0.94 + med_atual * 0.06 + np.random.normal(0, 0.03), 2))

        valor_atual = max(0.03, round(last["valor_atual"] + val_step + np.random.normal(0, 0.002), 3))
        valor_medio = max(0.03, round(last["valor_medio"] * 0.95 + valor_atual * 0.05 + np.random.normal(0, 0.001), 3))

        new_row = pd.DataFrame([{
            "timestamp": last["timestamp"] + timedelta(seconds=30),
            "transacoes_atual": trans_atual,
            "transacoes_media": trans_media,
            "med_atual": med_atual,
            "med_media": med_media,
            "valor_atual": valor_atual,
            "valor_medio": valor_medio,
        }])

        df = pd.concat([df, new_row], ignore_index=True).tail(120)
        st.session_state.tick += 1

        d_trans = pct_delta(trans_atual, trans_media)
        d_med = pct_delta(med_atual, med_media)

        if d_trans <= -12:
            append_event(f"Transações/min em queda: {d_trans:.1f}% abaixo da média.", "warn")
        elif d_trans >= 10:
            append_event(f"Transações/min acima da média: {d_trans:.1f}%.", "info")

        if d_med >= 12:
            append_event(f"Ritmo de MED/min acelerou: {d_med:.1f}%.", "warn")

    st.session_state.intrahora = df

    med_df = st.session_state.med_diario.copy()
    med_df.loc[med_df.index[-1], "MEDs"] = max(100, int(med_df.iloc[-1]["MEDs"] + np.random.normal(4, 3)))
    med_df.loc[med_df.index[-1], "Tratados"] = max(50, int(med_df.iloc[-1]["Tratados"] + np.random.normal(3, 2)))
    med_df.loc[med_df.index[-1], "Aguardando"] = max(10, int(med_df.iloc[-1]["Aguardando"] + np.random.normal(1, 2)))
    st.session_state.med_diario = med_df

    fin_df = st.session_state.financeiro_diario.copy()
    fin_df = ensure_finance_columns(fin_df)

    colunas_esperadas = {
        "Saldo Total": 11.80,
        "Saldo Bloqueado": 2.20,
        "Saldo PI": 3.24,
        "Saldo Treeal": 1.18,
    }

    for col, valor_padrao in colunas_esperadas.items():
        if col not in fin_df.columns:
            fin_df[col] = valor_padrao

    for col in colunas_esperadas.keys():
        fin_df.loc[fin_df.index[-1], col] = round(
            max(0.1, float(fin_df.loc[fin_df.index[-1], col]) + np.random.normal(0.02, 0.04)),
            2
        )

    st.session_state.financeiro_diario = fin_df

    sla_df = st.session_state.sla_diario.copy()
    sla_df.loc[sla_df.index[-1], "SLA (%)"] = round(min(99.9, max(92.0, sla_df.iloc[-1]["SLA (%)"] + np.random.normal(0.02, 0.12))), 2)
    sla_df.loc[sla_df.index[-1], "Tempo Médio (min)"] = round(min(8.0, max(2.0, sla_df.iloc[-1]["Tempo Médio (min)"] + np.random.normal(-0.02, 0.08))), 2)
    st.session_state.sla_diario = sla_df

# ============================================================
# BUILDERS
# ============================================================
def build_summaries():
    intra = st.session_state.intrahora
    med_df = st.session_state.med_diario
    fin_df = ensure_finance_columns(st.session_state.financeiro_diario.copy())
    sla_df = st.session_state.sla_diario
    filas = st.session_state.filas

    last = intra.iloc[-1]

    trans_delta = pct_delta(last["transacoes_atual"], last["transacoes_media"])
    med_delta = pct_delta(last["med_atual"], last["med_media"])
    valor_delta = pct_delta(last["valor_atual"], last["valor_medio"])

    saldo_total = round(float(fin_df.iloc[-1]["Saldo Total"]), 2)
    saldo_pi = round(float(fin_df.iloc[-1]["Saldo PI"]), 2)
    saldo_treeal = round(float(fin_df.iloc[-1]["Saldo Treeal"]), 2)

    return {
        "intra": {
            "transacoes_atual": int(last["transacoes_atual"]),
            "transacoes_media": int(last["transacoes_media"]),
            "transacoes_desvio": trans_delta,
            "transacoes_status": classify_trans_delta(trans_delta),
            "med_atual": float(last["med_atual"]),
            "med_media": float(last["med_media"]),
            "med_desvio": med_delta,
            "med_status": classify_med_delta(med_delta),
            "valor_atual": float(last["valor_atual"]),
            "valor_media": float(last["valor_medio"]),
            "valor_desvio": valor_delta,
            "valor_status": classify_valor_delta(valor_delta),
        },
        "med": {
            "tratados_pct": 96.79,
            "tratados": 6810,
            "aguardando_psp": 226,
            "transacoes": 19.4,
            "total_meds": 7036,
            "perc_med": 0.04,
            "nao_tratados": 226,
            "expiram_2d": 0,
            "vencidos": 1,
            "d0": 1,
            "ate_3_dias": 0,
            "acima_3_dias": 10,
            "status": "Crítico",
        },
        "fin": {
            "saldo_pi": saldo_pi,
            "perc_reservas": round(np.random.uniform(58, 64), 2),
            "pi_x_treeal": round(np.random.uniform(30, 38), 2),
            "saldo_cliente": round(np.random.uniform(1.0, 1.3), 2),
            "saldo_total": saldo_total,
            "saldo_ccme": round(np.random.uniform(4.8, 5.3), 2),
            "saldo_treeal": saldo_treeal,
            "status": "Atenção" if saldo_total > 10 else "Normal",
        },
        "trx": {
            "vol_transacionado": 473788,
            "var_d1": -29.76,
            "var_d7": -64.62,
            "status": classify_trans_delta(trans_delta),
        },
        "met": {
            "sla": float(sla_df.iloc[-1]["SLA (%)"]),
            "tempo_medio": float(sla_df.iloc[-1]["Tempo Médio (min)"]),
            "pendencias": int(filas["Pendentes"]),
            "falhas": int(filas["Falhas"]),
            "status": "Atenção" if filas["Pendentes"] >= 40 else "Normal",
        }
    }

def build_top_med_df():
    vals = []
    for v in st.session_state.top_med_base:
        vals.append(max(1, int(v + np.random.normal(0, max(1, v * 0.05)))))
    df = pd.DataFrame({
        "Cliente": st.session_state.top_med_names,
        "Transações": [144357, 468980, 765931, 1197, 717, 434, 2539, 128, 91, 106],
        "MEDs": vals,
    }).sort_values("MEDs", ascending=False).reset_index(drop=True)
    df["% MED"] = ((df["MEDs"] / df["Transações"]) * 100).round(2)
    df["Não tratados"] = [55, 167, 1, 0, 2, 1, 0, 0, 1, 0]
    df[">7d"] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    return df

def build_fin_contas_df():
    rows = []
    nomes = st.session_state.top_fin_names
    contas = st.session_state.top_fin_contas
    for i, nome in enumerate(nomes):
        saldo_total = round(max(0.5, [2.8, 2.3, 1.9, 1.6, 1.2][i] + np.random.normal(0, 0.08)), 2)
        saldo_bloq = round(max(0.05, [0.8, 0.6, 0.3, 0.25, 0.2][i] + np.random.normal(0, 0.03)), 2)
        rows.append({
            "Empresa": nome,
            "Conta": contas[i],
            "Saldo Total": saldo_total,
            "Saldo Bloqueado": min(saldo_total, saldo_bloq),
            "Transações Último Dia": max(1000, int([52000, 41400, 29800, 26700, 22100][i] + np.random.normal(0, 900)))
        })
    return pd.DataFrame(rows)

def build_top_trx_df():
    vals = []
    for v in st.session_state.top_trx_base:
        vals.append(max(1, int(v + np.random.normal(0, max(1, v * 0.03)))))
    df = pd.DataFrame({
        "Conta": [11941, 20003, 977, 136, 73, 63, 51, 22, 18, 12],
        "Cliente": st.session_state.top_trx_names,
        "D0": vals
    }).sort_values("D0", ascending=False).reset_index(drop=True)
    df["D0 x D-1"] = [round(np.random.uniform(-90, 350), 2) for _ in range(len(df))]
    df["D0 x D-7"] = [round(np.random.uniform(-90, 450), 2) for _ in range(len(df))]
    return df

def build_balance_df():
    horas = list(range(16))
    return pd.DataFrame({
        "Hora": horas,
        "Saldo Cliente": [2.7, 2.3, 1.9, 1.4, 1.1, 1.2, 1.5, 1.9, 2.2, 2.4, 3.0, 1.8, 1.1, 0.35, 0.8, 1.9],
        "Saldo Treeal": [1.4, 1.4, 1.4, 1.4, 1.4, 1.4, 1.4, 1.4, 1.4, 1.4, 1.4, 1.4, 1.4, 1.4, 1.4, 1.4],
        "% Consumo Bolso": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    })

def build_accum_balance_df():
    horas = list(range(16))
    return pd.DataFrame({
        "Hora": horas,
        "Linha Cinza": [6.8, 6.4, 6.0, 5.7, 5.4, 5.1, 4.7, 4.5, 4.6, 4.5, 4.2, 4.4, 5.0, 5.9, 6.3, 6.9],
        "Linha Laranja": [2.5, 2.2, 1.7, 1.3, 0.70, 1.2, 1.3, 1.4, 1.8, 2.2, 2.0, 2.1, 2.3, 2.5, 2.7, 3.0],
        "Linha Rosa": [2.3, 1.7, 1.3, 0.6, 1.1, 0.9, 1.0, 1.2, 1.1, 1.4, 1.5, 1.7, 2.0, 2.1, 2.5, 2.8]
    })

# ============================================================
# START
# ============================================================
init_state()

st.markdown('<div class="main-title">Painel Treeal Alertas</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub-title">Protótipo inspirado nas análises operacionais e financeiras — atualizado em {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}</div>',
    unsafe_allow_html=True
)

top_action_cols = st.columns([1, 1, 5])
with top_action_cols[0]:
    if st.button("Resetar sessão", use_container_width=True):
        init_state(force_reset=True)
        st.rerun()
with top_action_cols[1]:
    if st.button("Atualizar agora", use_container_width=True):
        update_simulation()
        st.rerun()

tab_home, tab_med, tab_fin, tab_trx, tab_met = st.tabs(
    ["🏠 Home", "🛡️ MED", "💰 Financeiro", "📈 Transações", "⚙️ Métricas"]
)

# ============================================================
# FILTERS OUTSIDE FRAGMENT
# ============================================================
with tab_home:
    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.segmented_control("Período", ["Hoje", "7 dias", "10 dias", "30 dias"], default="10 dias", key="home_periodo", width="stretch")
    with c2:
        st.segmented_control("Foco", ["Geral", "Críticos", "Atenção"], default="Geral", key="home_foco", width="stretch")
    with c3:
        st.multiselect("Empresas", st.session_state.top_med_names[:5], key="home_empresas")
    st.markdown('</div>', unsafe_allow_html=True)
    home_live = st.empty()

with tab_med:
    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.segmented_control("Período", ["Hoje", "7 dias", "10 dias", "30 dias"], default="10 dias", key="med_periodo", width="stretch")
    with c2:
        st.segmented_control("Status", ["Todos", "Críticos", "Abertos", "Tratados"], default="Todos", key="med_status", width="stretch")
    with c3:
        st.multiselect("Empresas", st.session_state.top_med_names, key="med_empresas")
    st.markdown('</div>', unsafe_allow_html=True)
    med_live = st.empty()

with tab_fin:
    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.segmented_control("Período", ["Hoje", "7 dias", "10 dias", "30 dias"], default="10 dias", key="fin_periodo", width="stretch")
    with c2:
        st.segmented_control("Visão", ["Saldo", "Reservas", "Balance"], default="Saldo", key="fin_visao", width="stretch")
    with c3:
        st.multiselect("Empresas", st.session_state.top_fin_names, key="fin_empresas")
    st.markdown('</div>', unsafe_allow_html=True)
    fin_live = st.empty()

with tab_trx:
    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.segmented_control("Período", ["Hoje", "7 dias", "10 dias", "30 dias"], default="Hoje", key="trx_periodo", width="stretch")
    with c2:
        st.segmented_control("Comparação", ["D-1", "D-7", "Média"], default="D-1", key="trx_comp", width="stretch")
    with c3:
        st.multiselect("Clientes", st.session_state.top_trx_names, key="trx_clientes")
    st.markdown('</div>', unsafe_allow_html=True)
    trx_live = st.empty()

with tab_met:
    st.markdown('<div class="filter-wrap">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.segmented_control("Período", ["Hoje", "7 dias", "10 dias", "30 dias"], default="10 dias", key="met_periodo", width="stretch")
    with c2:
        st.segmented_control("Visão", ["SLA", "Filas", "Eventos"], default="SLA", key="met_visao", width="stretch")
    with c3:
        st.multiselect("Escopo", ["Operação", "Processamento", "Reprocesso", "Suporte"], key="met_escopo")
    st.markdown('</div>', unsafe_allow_html=True)
    met_live = st.empty()

# ============================================================
# LIVE RENDER
# ============================================================
@st.fragment(run_every="30s")
def render_live():
    update_simulation()

    summaries = build_summaries()
    top_med = build_top_med_df()
    fin_contas = build_fin_contas_df()
    top_trx = build_top_trx_df()
    balance_df = build_balance_df()
    accum_balance_df = build_accum_balance_df()

    intra = st.session_state.intrahora.copy()
    med_diario = st.session_state.med_diario.copy()
    financeiro_diario = ensure_finance_columns(st.session_state.financeiro_diario.copy())
    sla_diario = st.session_state.sla_diario.copy()
    trans_intraday = st.session_state.trans_intraday.copy()
    filas_df = pd.DataFrame([{"Tipo": k, "Quantidade": v} for k, v in st.session_state.filas.items()])

    with home_live.container():
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Alertas críticos", 2)
        c2.metric("Alertas atenção", 3)
        c3.metric("Transações/min", fmt_int(summaries["intra"]["transacoes_atual"]), f"{summaries['intra']['transacoes_desvio']:.1f}%")
        c4.metric("MED/min", f"{summaries['intra']['med_atual']:.2f}", f"{summaries['intra']['med_desvio']:.1f}%")
        c5.metric("Valor/min", fmt_money_mi(summaries["intra"]["valor_atual"]), f"{summaries['intra']['valor_desvio']:.1f}%")

        st.markdown('<div class="section-title">Central de alertas</div>', unsafe_allow_html=True)

        a, b = st.columns(2)
        with a:
            render_status_card(
                "MED",
                summaries["med"]["status"],
                "Fila crítica e tratativa sob monitoramento.",
                f"Vencidos: {summaries['med']['vencidos']} | D0: {summaries['med']['d0']} | Acima de 3 dias: {summaries['med']['acima_3_dias']}"
            )
            render_status_card(
                "Financeiro",
                summaries["fin"]["status"],
                "Saldos, reservas e balance sob acompanhamento.",
                f"Saldo PI: {fmt_money_mi(summaries['fin']['saldo_pi'])} | Saldo Total: {fmt_money_mi(summaries['fin']['saldo_total'])}"
            )
        with b:
            render_status_card(
                "Transações",
                summaries["trx"]["status"],
                "Intra-hora e comparações D0 x D-1 x D-7.",
                f"Volume: {fmt_int(summaries['trx']['vol_transacionado'])} | D-1: {summaries['trx']['var_d1']}% | D-7: {summaries['trx']['var_d7']}%"
            )
            render_status_card(
                "Métricas",
                summaries["met"]["status"],
                "SLA, filas e eventos operacionais.",
                f"SLA: {summaries['met']['sla']:.2f}% | Pendências: {summaries['met']['pendencias']} | Falhas: {summaries['met']['falhas']}"
            )

        st.markdown('<div class="section-title">Monitoramento minuto a minuto</div>', unsafe_allow_html=True)

        x1, x2 = st.columns(2)
        with x1:
            st.subheader("Transações/min — Atual x Média")
            st.line_chart(intra.set_index("timestamp")[["transacoes_atual", "transacoes_media"]])
        with x2:
            st.subheader("MED/min — Atual x Média")
            st.line_chart(intra.set_index("timestamp")[["med_atual", "med_media"]])

        y1, y2 = st.columns(2)
        with y1:
            st.subheader("Valor/min — Atual x Média")
            st.line_chart(intra.set_index("timestamp")[["valor_atual", "valor_medio"]])
        with y2:
            st.subheader("Casos que exigem ação")
            for case in st.session_state.med_cases[:3]:
                render_med_case(case)

    with med_live.container():
        st.markdown('<div class="section-title">Tratativa dos MEDs</div>', unsafe_allow_html=True)

        k1, k2, k3 = st.columns([1.3, 1, 1])
        with k1:
            st.markdown(
                f"""
                <div class="soft-card">
                    <div style="font-size:1.1rem;font-weight:800;margin-bottom:8px;">Tratativa dos MEDs</div>
                    <div style="font-size:2rem;font-weight:800;">{summaries['med']['tratados_pct']:.2f}%</div>
                    <div class="muted">Tratados</div>
                    <div style="margin-top:12px;" class="muted">
                        Tratados: {fmt_int(summaries['med']['tratados'])}<br>
                        Aguardando PSP: {fmt_int(summaries['med']['aguardando_psp'])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with k2:
            st.metric("Transações", f"{summaries['med']['transacoes']:.1f}M", "▲ 8.3M")
            st.metric("% MED", f"{summaries['med']['perc_med']:.2f}%", "▼ 0.00 p.p.")

        with k3:
            st.metric("Total de MEDs", fmt_int(summaries['med']['total_meds']), "▲ 31.02%")
            st.metric("Não tratados", fmt_int(summaries['med']['nao_tratados']), f"{summaries['med']['expiram_2d']} expiram em 2d")

        st.markdown(
            f"""
            <div class="insight-box">
                <b>Resumo de criticidade</b><br>
                • Vencidos: {summaries['med']['vencidos']}<br>
                • D0: {summaries['med']['d0']}<br>
                • Até 3 dias para vencer: {summaries['med']['ate_3_dias']}<br>
                • Acima de 3 dias: {summaries['med']['acima_3_dias']}
            </div>
            """,
            unsafe_allow_html=True
        )

        a, b = st.columns(2)
        with a:
            st.subheader("Evolução diária")
            st.line_chart(med_diario.set_index("Dia")[["MEDs", "Tratados", "Aguardando"]])
        with b:
            st.subheader("Ritmo MED/min")
            st.line_chart(intra.set_index("timestamp")[["med_atual", "med_media"]])

        st.subheader("TOP 10 Ofensores MEDs")
        st.dataframe(top_med, use_container_width=True, hide_index=True)

        st.subheader("Fila crítica")
        for case in st.session_state.med_cases:
            render_med_case(case)

    with fin_live.container():
        st.markdown('<div class="section-title">Painel Financeiro</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Saldo PI", fmt_int(summaries["fin"]["saldo_pi"] * 1_000_000))
        c2.metric("% Reservas", f"{summaries['fin']['perc_reservas']:.2f}%")
        c3.metric("PI x Treeal", f"{summaries['fin']['pi_x_treeal']:.2f}%")

        c4, c5, c6 = st.columns(3)
        c4.metric("Saldo Cliente", fmt_int(summaries["fin"]["saldo_cliente"] * 1_000_000))
        c5.metric("Saldo Total", f"{summaries['fin']['saldo_total']:.2f}M")
        c6.metric("Saldo CCME", f"{summaries['fin']['saldo_ccme']:.2f}M")

        a, b = st.columns(2)
        with a:
            st.subheader("Saldo Clientes x Treeal")
            chart_df = balance_df.set_index("Hora")[["Saldo Cliente", "Saldo Treeal", "% Consumo Bolso"]]
            st.line_chart(chart_df)
        with b:
            st.subheader("Avg Accum. Balance")
            chart_df = accum_balance_df.set_index("Hora")[["Linha Cinza", "Linha Laranja", "Linha Rosa"]]
            st.line_chart(chart_df)

        st.subheader("Evolução de Saldos")
        chart_fin = financeiro_diario.set_index("Dia")[["Saldo PI", "Saldo Treeal", "Saldo Total", "Saldo Bloqueado"]]
        st.line_chart(chart_fin)

        st.subheader("Contas monitoradas")
        st.dataframe(fin_contas, use_container_width=True, hide_index=True)

    with trx_live.container():
        st.markdown('<div class="section-title">Resultado Geral</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("VOL. TRANSACIONADO", fmt_int(summaries["trx"]["vol_transacionado"]))
        c2.metric("VARIAÇÃO DO X D-1", f"{summaries['trx']['var_d1']:.2f}%", "▼ 200.742")
        c3.metric("VARIAÇÃO DO X D-7", f"{summaries['trx']['var_d7']:.2f}%", "▼ 865.192")

        st.subheader("Intra-hora")
        st.line_chart(trans_intraday.set_index("Hora")[["D0", "D-1", "D-7"]])

        a, b = st.columns(2)
        with a:
            st.subheader("Transações/min — Atual x Média")
            st.line_chart(intra.set_index("timestamp")[["transacoes_atual", "transacoes_media"]])
        with b:
            st.subheader("Últimos sinais")
            for ev in st.session_state.event_log[:8]:
                color = "#22c55e" if ev["nivel"] == "info" else "#f59e0b"
                st.markdown(
                    f"""
                    <div class="event-box">
                        <div class="muted">{ev['hora']}</div>
                        <div style="font-weight:700;color:{color};">{ev['mensagem']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.subheader("Top 10 Contas")
        st.dataframe(top_trx, use_container_width=True, hide_index=True)

    with met_live.container():
        st.markdown('<div class="section-title">Métricas Operacionais</div>', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("SLA", f"{summaries['met']['sla']:.2f}%")
        c2.metric("Tempo médio", f"{summaries['met']['tempo_medio']:.2f} min")
        c3.metric("Pendências", summaries["met"]["pendencias"])
        c4.metric("Falhas", summaries["met"]["falhas"])

        a, b = st.columns(2)
        with a:
            st.subheader("SLA e Tempo Médio")
            st.line_chart(sla_diario.set_index("Dia")[["SLA (%)", "Tempo Médio (min)"]])
        with b:
            st.subheader("Distribuição de filas")
            st.bar_chart(filas_df.set_index("Tipo")["Quantidade"])

        st.subheader("Eventos operacionais")
        for ev in st.session_state.event_log[:12]:
            color = "#22c55e" if ev["nivel"] == "info" else "#f59e0b"
            st.markdown(
                f"""
                <div class="event-box">
                    <div class="muted">{ev['hora']}</div>
                    <div style="font-weight:700;color:{color};">{ev['mensagem']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

render_live()