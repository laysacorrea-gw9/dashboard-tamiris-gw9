import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import locale

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Dashboard Financeiro - Dra. Tamiris",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Mapa de meses pt-BR
MESES_PT = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}
MESES_PT_CURTO = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}

def fmt_brl(valor):
    """Formata valor em R$ brasileiro"""
    if abs(valor) >= 1000:
        return f"R$ {valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def mes_label_pt(ano_mes_str):
    """Converte '2026-01' para 'Janeiro/2026'"""
    dt = pd.to_datetime(ano_mes_str)
    return f"{MESES_PT[dt.month]}/{dt.year}"

def mes_label_curto(ano_mes_str):
    """Converte '2026-01' para 'Jan/26'"""
    dt = pd.to_datetime(ano_mes_str)
    return f"{MESES_PT_CURTO[dt.month]}/{str(dt.year)[2:]}"

# CSS customizado - clean e feminino
st.markdown("""
<style>
    .main .block-container { padding-top: 1rem; max-width: 1400px; }

    /* Cards roxos */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] label p,
    div[data-testid="stMetric"] label span { color: rgba(255,255,255,0.9) !important; font-size: 0.9rem !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"],
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] p,
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] span { color: white !important; font-size: 1.8rem !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"],
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] p,
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] span { color: rgba(255,255,255,0.9) !important; }

    h1 { color: #2d3436; font-size: 2rem !important; }
    h2 { color: #2d3436; font-size: 1.5rem !important; }
    h3 { color: #636e72; font-size: 1.2rem !important; }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6; border-radius: 10px;
        padding: 10px 20px; font-size: 1rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6c5ce7 !important; color: white !important;
    }

    /* Botoes seta do mes */
    div[data-testid="stButton"] > button[kind="secondary"] {
        border: none !important; background: transparent !important;
        color: #636e72 !important; font-size: 1.3rem !important;
        padding: 4px 8px !important; min-height: 0 !important;
    }
    div[data-testid="stButton"] > button[kind="secondary"]:hover {
        color: #6c5ce7 !important; background: #f0f0f0 !important;
        border-radius: 50% !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CLASSIFICACAO DE CATEGORIAS
# ============================================================
CATEGORIAS_FIXAS = [
    'Aluguel/Financiamento', 'Aluguel Consultório', 'Academia',
    'Assinaturas m', 'Assinatura / Financiamento', 'Tarifas / Assinaturas',
    'Internet / Telefone', 'Contas', 'Contas - Consultório',
    'Seguros', 'Plano de Saúde', 'Planejamento Financeiro',
    'Condomínio', 'IPTU / IPVA', 'Simples Nacional', 'Impostos',
    'Trabalho - Consultório Geral', 'Secretária', 'Contabilidade',
    'Empregados / Faxineira', 'Empregados / Funcionários',
    'Educação', 'Educação Filho', 'Dividas', 'Repasses', 'Marketing'
]

CATEGORIAS_VARIAVEIS = [
    'Alimentação', 'Restaurante / Ifood', 'Compras Geral', 'Compras Moradia',
    'Uber / 99', 'Combustível', 'Farmácia', 'Lazer Geral',
    'Cuidados pessoais Geral', 'Estética e Tratamentos',
    'Roupa / Sapatos / Vestuário', 'Pedágio / Estacionamento',
    'Transporte Geral', 'Mercado', 'Beleza / Estética', 'Pet',
    'Presentes', 'Viagem', 'Viagens', 'Insumos / Materiais',
    'Bares / Festas', 'Saúde Geral',
    'Psciologo / Nutri / Fisio (Terapias)',
    'Tecnologia / Diversas', 'Manutenção / Revisão',
    'Ajuda Familiares / Terceiros'
]

def classificar_tipo_despesa(categoria):
    if categoria in CATEGORIAS_FIXAS:
        return 'Fixa'
    elif categoria in CATEGORIAS_VARIAVEIS:
        return 'Variável'
    else:
        return 'Outros'

# Mapeamento subcategoria → categoria mãe (igual Planfi)
CATEGORIA_MAE = {}
MAPA_CATEGORIAS = {
    'Alimentação': ['Alimentação', 'Restaurante / Ifood', 'Bares / Festas'],
    'Compras': ['Compras Geral', 'Compras Moradia', 'Roupa / Sapatos / Vestuário'],
    'Cuidados Pessoais': ['Cuidados pessoais Geral', 'Academia', 'Estética e Tratamentos', 'Psciologo / Nutri / Fisio (Terapias)'],
    'Dívidas': ['Dividas', 'IOF / Tarifas', 'Juros/ IOF / Tarifas'],
    'Educação': ['Educação'],
    'Impostos': ['Impostos'],
    'Lazer': ['Lazer Geral', 'Presentes', 'Tecnologia / Diversas'],
    'Moradia / Casa': ['Aluguel/Financiamento', 'Contas', 'Manutenção / Revisão', 'Empregados / Faxineira', 'Assinaturas m', 'Tarifas / Assinaturas'],
    'Outros': ['Outros'],
    'Planejamento': ['Planejamento Financeiro'],
    'Saúde': ['Farmácia', 'Saúde Geral', 'Seguros'],
    'Consultório': ['Trabalho - Consultório Geral', 'Aluguel Consultório', 'Contas - Consultório', 'Insumos / Materiais', 'Marketing', 'Empregados / Funcionários', 'Repasses', 'Contabilidade', 'Consultório'],
    'Transporte': ['Combustível', 'Uber / 99', 'Pedágio / Estacionamento', 'Transporte Geral', 'Assinatura / Financiamento'],
    'Viagens': ['Viagens'],
    'Ajuda Familiares': ['Ajuda Familiares / Terceiros'],
}
for mae, subs in MAPA_CATEGORIAS.items():
    for sub in subs:
        CATEGORIA_MAE[sub] = mae

def get_categoria_mae(cat):
    return CATEGORIA_MAE.get(cat, cat)

# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data(ttl=30)  # recarrega a cada 30 segundos
def load_data(file_path=None, uploaded_file=None):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    elif file_path and os.path.exists(file_path):
        df = pd.read_csv(file_path, encoding='utf-8')
    else:
        return None

    df['Valor_num'] = df['Valor'].str.replace('R$ ', '', regex=False)\
                                  .str.replace('.', '', regex=False)\
                                  .str.replace(',', '.', regex=False)\
                                  .astype(float)

    df['Data_parsed'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
    df['Ano_Mes'] = df['Data_parsed'].dt.strftime('%Y-%m')

    df['Categoria'] = df['Categoria'].fillna('Sem Categoria')
    df['Conta'] = df['Conta'].fillna('Sem Conta')
    df['Descrição'] = df['Descrição'].fillna('')

    df['Tipo_Despesa'] = df['Categoria'].apply(classificar_tipo_despesa)
    df['Categoria_Mae'] = df['Categoria'].apply(get_categoria_mae)

    # Gerar projeção para meses futuros (Abr-Set 2026)
    df = gerar_projecao(df)

    return df

def gerar_projecao(df):
    """Gera lançamentos projetados para Abr-Set 2026 baseado no padrão dos últimos 6 meses"""
    todos_meses = sorted(df['Ano_Mes'].unique())
    mes_vigente = todos_meses[-1]
    meses_anteriores = [m for m in todos_meses if m < mes_vigente]
    ultimos_6m = meses_anteriores[-6:] if len(meses_anteriores) >= 6 else meses_anteriores
    df_base = df[df['Ano_Mes'].isin(ultimos_6m)]
    n = len(ultimos_6m)
    if n == 0:
        return df

    # Calcular média por categoria (despesas)
    media_por_cat = df_base[df_base['Tipo'] == 'EXPENSE'].groupby('Categoria')['Valor_num'].sum() / n

    # Calcular média por categoria (receitas)
    media_rec_cat = df_base[df_base['Tipo'] == 'INCOME'].groupby('Categoria')['Valor_num'].sum() / n

    meses_futuros = ['2026-04', '2026-05', '2026-06', '2026-07', '2026-08', '2026-09']
    parcelas_viagem = 2805  # até junho
    protesto_mensal = 2000  # até junho

    rows = []
    for mes in meses_futuros:
        tem_parcela = mes <= '2026-06'

        # Receitas projetadas (95% da média)
        for cat, val in media_rec_cat.items():
            rows.append({
                'Data': f'01/{mes[5:7]}/{mes[:4]}',
                'Tipo': 'INCOME',
                'Valor': f'R$ {val * 0.95:,.2f}',
                'Valor_num': val * 0.95,
                'Descrição': f'[Projeção] {cat}',
                'Categoria': cat,
                'Conta': 'Projeção',
                'Tipo_Despesa': 'Outros',
                'Categoria_Mae': get_categoria_mae(cat),
                'Data_parsed': pd.to_datetime(f'{mes}-01'),
                'Ano_Mes': mes,
                'Recorrente': 'Não', 'Status': 'PROJECTED',
                'Tipo_Recorrência': '', 'Limite_Recorrência': '',
                'Data_Criação': '', 'Data_Atualização': ''
            })

        # Despesas projetadas
        for cat, val in media_por_cat.items():
            rows.append({
                'Data': f'01/{mes[5:7]}/{mes[:4]}',
                'Tipo': 'EXPENSE',
                'Valor': f'R$ {val:,.2f}',
                'Valor_num': val,
                'Descrição': f'[Projeção] {cat}',
                'Categoria': cat,
                'Conta': 'Projeção',
                'Tipo_Despesa': classificar_tipo_despesa(cat),
                'Categoria_Mae': get_categoria_mae(cat),
                'Data_parsed': pd.to_datetime(f'{mes}-01'),
                'Ano_Mes': mes,
                'Recorrente': 'Não', 'Status': 'PROJECTED',
                'Tipo_Recorrência': '', 'Limite_Recorrência': '',
                'Data_Criação': '', 'Data_Atualização': ''
            })

        # Parcelas viagem (até junho)
        if tem_parcela:
            rows.append({
                'Data': f'01/{mes[5:7]}/{mes[:4]}',
                'Tipo': 'EXPENSE',
                'Valor': f'R$ {parcelas_viagem:,.2f}',
                'Valor_num': parcelas_viagem,
                'Descrição': '[Projeção] Parcelas viagem Londres',
                'Categoria': 'Viagens',
                'Conta': 'Projeção',
                'Tipo_Despesa': 'Variável',
                'Categoria_Mae': 'Viagens',
                'Data_parsed': pd.to_datetime(f'{mes}-01'),
                'Ano_Mes': mes,
                'Recorrente': 'Não', 'Status': 'PROJECTED',
                'Tipo_Recorrência': '', 'Limite_Recorrência': '',
                'Data_Criação': '', 'Data_Atualização': ''
            })

            # Protestos
            rows.append({
                'Data': f'01/{mes[5:7]}/{mes[:4]}',
                'Tipo': 'EXPENSE',
                'Valor': f'R$ {protesto_mensal:,.2f}',
                'Valor_num': protesto_mensal,
                'Descrição': '[Projeção] Pagamento protestos cartório',
                'Categoria': 'Dividas',
                'Conta': 'Projeção',
                'Tipo_Despesa': 'Fixa',
                'Categoria_Mae': 'Dívidas',
                'Data_parsed': pd.to_datetime(f'{mes}-01'),
                'Ano_Mes': mes,
                'Recorrente': 'Não', 'Status': 'PROJECTED',
                'Tipo_Recorrência': '', 'Limite_Recorrência': '',
                'Data_Criação': '', 'Data_Atualização': ''
            })

    if rows:
        df_proj = pd.DataFrame(rows)
        # Garantir mesmas colunas
        for col in df.columns:
            if col not in df_proj.columns:
                df_proj[col] = ''
        df = pd.concat([df, df_proj[df.columns]], ignore_index=True)

    return df

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.image("https://gw9capital.com.br/wp-content/uploads/2024/03/LOGO-BRANCA.png", width=180)
    st.markdown("---")
    st.markdown("### 👩🏻‍⚕️ Dra. Tamiris Paiva")
    st.markdown("**Médica** · 35 anos")
    st.markdown("**Assessora:** Laysa Corrêa")
    st.markdown("---")

    # Navegação estilo balão com botões
    if 'pagina' not in st.session_state:
        st.session_state.pagina = "mes"

    menu_items = [
        ("mes", "📊  Mês a Mês"),
        ("detalhe", "🔍  Detalhamento"),
        ("alertas", "⚠️  Alertas"),
    ]

    for key, label in menu_items:
        is_active = st.session_state.pagina == key
        if is_active:
            st.markdown(
                f"<div style='background:linear-gradient(135deg,#667eea,#764ba2); "
                f"color:white; padding:10px 14px; border-radius:10px; "
                f"margin-bottom:6px; font-size:0.9rem; font-weight:600;'>"
                f"{label}</div>", unsafe_allow_html=True
            )
        else:
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.pagina = key
                st.rerun()

    pagina = st.session_state.pagina

    st.markdown("---")

    default_csv = os.path.join(os.path.dirname(__file__), "Planfi", "Planfi - set.2025 a 03.2026.csv")
    uploaded = st.file_uploader("📂 Carregar novo CSV", type=['csv'])

    if uploaded:
        df = load_data(uploaded_file=uploaded)
    else:
        df = load_data(file_path=default_csv)

    if df is None:
        st.error("Nenhum CSV encontrado.")
        st.stop()

# ============================================================
# HEADER
# ============================================================
st.markdown("# 💰 Suas Finanças, Tamiris")

meses_disponiveis = sorted(df['Ano_Mes'].unique())

if pagina == "mes":
    # ---- MÊS A MÊS: seletor + cards do mês ----
    if 'idx_mes' not in st.session_state:
        st.session_state.idx_mes = len(meses_disponiveis) - 1

    col_espacoL, col_esq, col_mes_sel, col_dir, col_espacoR = st.columns([2, 0.3, 1.5, 0.3, 2])
    with col_esq:
        if st.button("◁", key="btn_esq", help="Mês anterior"):
            if st.session_state.idx_mes > 0:
                st.session_state.idx_mes -= 1
                st.rerun()
    with col_mes_sel:
        st.markdown(
            f"<div style='text-align:center; font-size:1.1rem; font-weight:600; "
            f"color:#2d3436; padding:6px 16px; border:1.5px solid #b2bec3; "
            f"border-radius:20px; background:white; white-space:nowrap;'>"
            f"{mes_label_pt(meses_disponiveis[st.session_state.idx_mes])}"
            f"</div>",
            unsafe_allow_html=True
        )
    with col_dir:
        if st.button("▷", key="btn_dir", help="Próximo mês"):
            if st.session_state.idx_mes < len(meses_disponiveis) - 1:
                st.session_state.idx_mes += 1
                st.rerun()

    mes_selecionado = meses_disponiveis[st.session_state.idx_mes]
    is_projecao = mes_selecionado >= '2026-04'
    df_mes = df[df['Ano_Mes'] == mes_selecionado]
    receitas_mes = df_mes[df_mes['Tipo'] == 'INCOME']
    despesas_mes = df_mes[df_mes['Tipo'] == 'EXPENSE']
    entrou = receitas_mes['Valor_num'].sum()
    saiu = despesas_mes['Valor_num'].sum()
    saldo_mes = entrou - saiu

    if is_projecao:
        st.markdown(
            """<div style="background:#6c5ce7; color:white; padding:8px 16px; border-radius:8px;
            text-align:center; font-size:0.9rem; margin-bottom:10px;">
            🔮 <b>PROJEÇÃO</b> — valores estimados baseados no seu padrão de consumo (Set/25 a Fev/26)
            </div>""", unsafe_allow_html=True
        )

    # Despesas fixas/variáveis do mês
    desp_fixas_mes = despesas_mes[despesas_mes['Categoria'].isin(CATEGORIAS_FIXAS)]['Valor_num'].sum()
    desp_var_mes = despesas_mes[despesas_mes['Categoria'].isin(CATEGORIAS_VARIAVEIS)]['Valor_num'].sum()
    desp_outros_mes = saiu - desp_fixas_mes - desp_var_mes

    bal_cor = "#00b894" if saldo_mes >= 0 else "#d63031"
    bal_label = "✅ Sobrou" if saldo_mes >= 0 else "❌ Faltou"
    bal_icon = "💚" if saldo_mes >= 0 else "🔴"

    col_e, col_s, col_b = st.columns([2, 2, 1])

    with col_e:
        st.markdown(
            f"""<div style="background:linear-gradient(135deg, #00b894, #55efc4);
            padding:25px; border-radius:16px; color:white; text-align:center;
            box-shadow: 0 4px 15px rgba(0,184,148,0.3); height:180px;
            display:flex; flex-direction:column; justify-content:center;">
            <div style="font-size:0.95rem; opacity:0.9;">💚 Entrou</div>
            <div style="font-size:2.2rem; font-weight:bold; margin-top:8px;">{fmt_brl(entrou)}</div>
            </div>""", unsafe_allow_html=True
        )

    with col_s:
        st.markdown(
            f"""<div style="background:linear-gradient(135deg, #e17055, #fd79a8);
            padding:15px; border-radius:16px; color:white; text-align:center;
            box-shadow: 0 4px 15px rgba(225,112,85,0.3);">
            <div style="font-size:0.95rem; opacity:0.9;">🔴 Saiu</div>
            <div style="font-size:1.8rem; font-weight:bold; margin:5px 0;">{fmt_brl(saiu)}</div>
            <div style="display:flex; gap:8px; margin-top:8px;">
                <div style="flex:1; background:rgba(255,255,255,0.2); border-radius:10px; padding:10px;">
                    <div style="font-size:0.75rem; opacity:0.85;">🔒 Fixos</div>
                    <div style="font-size:1.1rem; font-weight:bold;">{fmt_brl(desp_fixas_mes)}</div>
                </div>
                <div style="flex:1; background:rgba(255,255,255,0.2); border-radius:10px; padding:10px;">
                    <div style="font-size:0.75rem; opacity:0.85;">🔄 Variáveis</div>
                    <div style="font-size:1.1rem; font-weight:bold;">{fmt_brl(desp_var_mes)}</div>
                </div>
                <div style="flex:1; background:rgba(255,255,255,0.2); border-radius:10px; padding:10px;">
                    <div style="font-size:0.75rem; opacity:0.85;">📦 Outros</div>
                    <div style="font-size:1.1rem; font-weight:bold;">{fmt_brl(desp_outros_mes)}</div>
                </div>
            </div>
            </div>""", unsafe_allow_html=True
        )

    with col_b:
        st.markdown(
            f"""<div style="background:{bal_cor};
            padding:25px; border-radius:16px; color:white; text-align:center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15); height:180px;
            display:flex; flex-direction:column; justify-content:center;">
            <div style="font-size:0.95rem; opacity:0.9;">{bal_icon} {bal_label}</div>
            <div style="font-size:2.2rem; font-weight:bold; margin-top:8px;">{fmt_brl(abs(saldo_mes))}</div>
            </div>""", unsafe_allow_html=True
        )

elif pagina == "detalhe":
    # ---- DETALHAMENTO: cards do ANO (acumulado) ----
    periodo_txt = f"{mes_label_curto(meses_disponiveis[0])} a {mes_label_curto(meses_disponiveis[-1])}"
    st.markdown(f"**Período:** {periodo_txt} · **{len(df):,} transações**")

    total_receita = df[df['Tipo'] == 'INCOME']['Valor_num'].sum()
    total_despesa = df[df['Tipo'] == 'EXPENSE']['Valor_num'].sum()
    balanco_total = total_receita - total_despesa
    pp = balanco_total / max(total_receita, 1) * 100

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("💚 Receita Total", fmt_brl(total_receita))
    with c2:
        st.metric("🔴 Despesa Total", fmt_brl(total_despesa))
    with c3:
        st.metric("📊 Balanço", fmt_brl(balanco_total))
    with c4:
        st.metric("💰 Poupança", f"{pp:.1f}%")

st.markdown("---")

# ============================================================
# PAGINAS (baseado na sidebar)
# ============================================================
if pagina == "mes":
    # Alerta sem categoria (amarelo)
    sem_cat = df_mes[df_mes['Categoria'] == 'Sem Categoria']
    if len(sem_cat) > 0:
        total_sem_cat = sem_cat['Valor_num'].sum()
        st.markdown(
            f"""<div style="background:#FFD600; color:#000; padding:10px 16px; border-radius:10px;
            font-weight:bold; font-size:0.9rem; margin:10px 0;
            box-shadow: 0 2px 8px rgba(255,214,0,0.4);">
            ⚠️ {len(sem_cat)} transações sem categoria ({fmt_brl(total_sem_cat)}) — categorize no Planfi!
            </div>""", unsafe_allow_html=True
        )

    st.markdown("")

    # DESPESAS EM PIZZA + RECEITAS EM BARRA
    col_desp, col_rec = st.columns(2)

    with col_desp:
        st.markdown("### 🍕 Pra onde foi seu dinheiro")

        # Agrupar por categoria mãe (igual Planfi)
        desp_cat = despesas_mes.groupby('Categoria_Mae')['Valor_num'].sum().sort_values(ascending=False)
        # Renomear "Sem Categoria" pra destacar
        desp_cat = desp_cat.rename(index={'Sem Categoria': '⚠️ Sem Categoria'})
        total_desp = desp_cat.sum()

        if total_desp > 0:
            desp_pct = desp_cat / total_desp * 100
            # Categorias com menos de 3% viram "Outros"
            principais = desp_pct[desp_pct >= 3]
            outros = desp_pct[desp_pct < 3]

            valores_pizza = list(desp_cat[principais.index].values)
            nomes_pizza = list(principais.index)

            if len(outros) > 0:
                valores_pizza.append(desp_cat[outros.index].sum())
                nomes_pizza.append(f'Outros ({len(outros)} categorias)')

            # Cores bonitas
            cores = ['#6c5ce7', '#00b894', '#fd79a8', '#fdcb6e', '#e17055',
                     '#74b9ff', '#a29bfe', '#55efc4', '#fab1a0', '#dfe6e9',
                     '#b2bec3', '#636e72', '#00cec9', '#e84393', '#0984e3']

            # Destacar "Sem Categoria" com cor vermelha e pull
            cores_pizza = []
            pull_pizza = []
            for i, nome in enumerate(nomes_pizza):
                if '⚠️ Sem Categoria' in nome:
                    cores_pizza.append('#FFD600')
                    pull_pizza.append(0.15)
                else:
                    cores_pizza.append(cores[i % len(cores)])
                    pull_pizza.append(0)

            fig_pizza = go.Figure(data=[go.Pie(
                labels=nomes_pizza,
                values=valores_pizza,
                hole=0.4,
                textinfo='label+percent+value',
                texttemplate='%{label}<br>%{percent}<br><b>R$ %{value:,.0f}</b>',
                textposition='outside',
                textfont_size=14,
                marker_colors=cores_pizza,
                pull=pull_pizza
            )])

            fig_pizza.update_layout(
                height=450,
                margin=dict(t=20, b=20, l=20, r=20),
                showlegend=False,
                annotations=[dict(
                    text=f'<b>{fmt_brl(total_desp)}</b>',
                    x=0.5, y=0.5, font_size=16, showarrow=False
                )]
            )
            # Gráfico interativo - clique na fatia filtra a tabela
            evento = st.plotly_chart(fig_pizza, use_container_width=True,
                                      on_select="rerun", key="pizza_click")

            # Capturar clique na pizza
            if evento and evento.selection and evento.selection.points:
                cat_clicada = evento.selection.points[0].get('label', None)
                if cat_clicada:
                    if cat_clicada == st.session_state.filtro_cat_pizza:
                        st.session_state.filtro_cat_pizza = None
                    else:
                        st.session_state.filtro_cat_pizza = cat_clicada
                    st.rerun()
        else:
            st.info("Sem despesas neste mês")

    with col_rec:
        st.markdown("### 💰 De onde veio seu dinheiro")

        rec_cat = receitas_mes.groupby('Categoria')['Valor_num'].sum().sort_values(ascending=True)

        if len(rec_cat) > 0:
            fig_rec = go.Figure(data=[go.Bar(
                y=rec_cat.index,
                x=rec_cat.values,
                orientation='h',
                marker_color=['#00b894', '#55efc4', '#81ecec', '#74b9ff',
                              '#a29bfe', '#6c5ce7', '#dfe6e9', '#b2bec3',
                              '#fdcb6e', '#fab1a0', '#e17055'][:len(rec_cat)],
                text=[fmt_brl(v) for v in rec_cat.values],
                textposition='inside',
                textfont=dict(size=14, color='white'),
                insidetextanchor='middle'
            )])

            max_val = rec_cat.max()
            fig_rec.update_layout(
                height=450,
                margin=dict(t=20, b=20, l=10, r=20),
                xaxis_title="",
                yaxis_title="",
                showlegend=False,
                xaxis=dict(range=[0, max_val * 1.1])
            )
            fig_rec.update_xaxes(visible=False)
            st.plotly_chart(fig_rec, use_container_width=True)
        else:
            st.info("Sem receitas neste mês")

    # TABELA DE LANÇAMENTOS DO MÊS com filtros
    st.markdown("---")
    st.markdown(f"### 📄 Lançamentos de {mes_label_pt(mes_selecionado)}")

    df_tabela_mes = df_mes[['Data', 'Tipo', 'Valor', 'Valor_num', 'Descrição', 'Categoria', 'Categoria_Mae', 'Conta']].copy()
    df_tabela_mes['Tipo_label'] = df_tabela_mes['Tipo'].map({'INCOME': '💚 Entrada', 'EXPENSE': '🔴 Saída'})

    # Botões de categoria (clicáveis como a pizza)
    cats_despesa = despesas_mes.groupby('Categoria_Mae')['Valor_num'].sum().sort_values(ascending=False)
    total_desp_btns = cats_despesa.sum()

    # Identificar quais categorias são "Outros" (menos de 3%)
    if total_desp_btns > 0:
        cats_pct = cats_despesa / total_desp_btns * 100
        cats_principais = cats_pct[cats_pct >= 3].index.tolist()
        cats_outros = cats_pct[cats_pct < 3].index.tolist()
    else:
        cats_principais = []
        cats_outros = []

    # Lista de botões: principais + "Outros (X categorias)"
    cat_list = cats_principais.copy()
    if len(cats_outros) > 0:
        cat_list.append(f"Outros ({len(cats_outros)} categorias)")

    if 'filtro_cat_pizza' not in st.session_state:
        st.session_state.filtro_cat_pizza = None

    st.markdown("**Clique numa categoria pra filtrar:**")
    cols_por_linha = 5
    for i in range(0, len(cat_list), cols_por_linha):
        cols = st.columns(cols_por_linha)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(cat_list):
                cat = cat_list[idx]
                val = cats_despesa.get(cat, 0)
                is_active = st.session_state.filtro_cat_pizza == cat
                is_sem_cat = cat == 'Sem Categoria'
                label = f"{'✅ ' if is_active else ''}{'⚠️ ' if is_sem_cat else ''}{cat}"
                with col:
                    if is_sem_cat:
                        st.markdown(
                            f"<style>div[data-testid='stButton'] button[kind='secondary']:has(p:contains('Sem Categoria')) "
                            f"{{ background: #FFD600 !important; color: #000 !important; font-weight: bold !important; }}</style>",
                            unsafe_allow_html=True
                        )
                    if st.button(label, key=f"cat_btn_{idx}", use_container_width=True, type="primary" if is_sem_cat else "secondary"):
                        if st.session_state.filtro_cat_pizza == cat:
                            st.session_state.filtro_cat_pizza = None
                        else:
                            st.session_state.filtro_cat_pizza = cat
                        st.rerun()

    # Botão limpar filtro
    if st.session_state.filtro_cat_pizza:
        if st.button("❌ Limpar filtro", key="limpar_cat"):
            st.session_state.filtro_cat_pizza = None
            st.rerun()

    st.markdown("")

    # Filtros adicionais
    fc1, fc2 = st.columns(2)
    with fc1:
        contas_mes = sorted(df_tabela_mes['Conta'].unique())
        filtro_conta = st.multiselect("Conta:", contas_mes, key="filtro_conta_mes")
    with fc2:
        busca_desc = st.text_input("🔍 Buscar na descrição:", key="busca_desc_mes")

    # Aplicar filtros
    df_show = df_tabela_mes.copy()
    if st.session_state.filtro_cat_pizza:
        filtro = st.session_state.filtro_cat_pizza
        if 'Outros (' in str(filtro):
            df_show = df_show[df_show['Categoria_Mae'].isin(cats_outros)]
        elif '⚠️ Sem Categoria' in str(filtro):
            df_show = df_show[df_show['Categoria'] == 'Sem Categoria']
        else:
            df_show = df_show[df_show['Categoria_Mae'] == filtro]
    if filtro_conta:
        df_show = df_show[df_show['Conta'].isin(filtro_conta)]
    if busca_desc:
        df_show = df_show[df_show['Descrição'].str.contains(busca_desc, case=False, na=False)]

    # Totais filtrados
    total_filtrado = df_show['Valor_num'].sum()
    filtro_txt = f" · Filtro: **{st.session_state.filtro_cat_pizza}**" if st.session_state.filtro_cat_pizza else ""
    st.markdown(f"**{len(df_show)} lançamentos** · Total: **{fmt_brl(total_filtrado)}**{filtro_txt}")

    st.dataframe(
        df_show[['Data', 'Tipo_label', 'Valor', 'Descrição', 'Categoria', 'Conta']]\
            .rename(columns={'Tipo_label': 'Tipo'})\
            .sort_values('Data', ascending=False),
        use_container_width=True, height=400, hide_index=True
    )


# ============================================================
# PAGINA 2 - DETALHAMENTO (VISÃO DO ANO)
# ============================================================
elif pagina == "detalhe":
    st.markdown("### 🔍 Visão do Ano")

    # HISTÓRICO MENSAL - simples: sobrou ou faltou por mês
    st.markdown("#### 📊 Sobrou ou faltou em cada mês?")

    resumo_mensal = df.groupby(['Ano_Mes', 'Tipo'])['Valor_num'].sum().unstack(fill_value=0)
    if 'INCOME' not in resumo_mensal.columns:
        resumo_mensal['INCOME'] = 0
    if 'EXPENSE' not in resumo_mensal.columns:
        resumo_mensal['EXPENSE'] = 0
    resumo_mensal['Saldo'] = resumo_mensal['INCOME'] - resumo_mensal['EXPENSE']
    resumo_mensal = resumo_mensal.sort_index()

    meses_hist = resumo_mensal.index.tolist()
    meses_hist_label = [mes_label_curto(m) for m in meses_hist]
    cores_saldo = ['#00b894' if v >= 0 else '#e17055' for v in resumo_mensal['Saldo']]

    fig_hist = go.Figure()
    fig_hist.add_trace(go.Bar(
        x=meses_hist_label,
        y=resumo_mensal['Saldo'],
        marker_color=cores_saldo,
        text=[fmt_brl(v) for v in resumo_mensal['Saldo']],
        textposition='outside',
        textfont_size=13
    ))
    fig_hist.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig_hist.update_layout(
        height=350,
        margin=dict(t=20, b=20),
        yaxis_visible=False,
        showlegend=False,
        xaxis_title=""
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("<div style='text-align:center; color:#636e72; font-size:0.85rem;'>"
                "🟢 Verde = sobrou dinheiro · 🔴 Vermelho = gastou mais do que recebeu"
                "</div>", unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔒 Gastos Fixos vs Variáveis")
        desp_all = df[df['Tipo'] == 'EXPENSE']
        desp_tipo = desp_all.groupby(['Ano_Mes', 'Tipo_Despesa'])['Valor_num'].sum().reset_index()
        desp_tipo['Mês'] = desp_tipo['Ano_Mes'].apply(mes_label_curto)

        fig_fixvar = px.bar(
            desp_tipo, x='Mês', y='Valor_num', color='Tipo_Despesa',
            barmode='stack',
            color_discrete_map={'Fixa': '#6c5ce7', 'Variável': '#e17055', 'Outros': '#fdcb6e'},
            labels={'Valor_num': '', 'Tipo_Despesa': ''}
        )
        fig_fixvar.update_layout(height=400, margin=dict(t=10), yaxis_tickformat=",.0f")
        st.plotly_chart(fig_fixvar, use_container_width=True)

    with col2:
        st.markdown("#### 🏆 Onde você mais gasta (no ano)")
        # Só dados reais (sem projeção)
        desp_reais = desp_all[desp_all['Ano_Mes'] < '2026-04']
        n_meses_reais = desp_reais['Ano_Mes'].nunique()
        top_mae = desp_reais.groupby('Categoria_Mae')['Valor_num'].sum().sort_values(ascending=True).tail(8)

        fig_top = go.Figure(data=[go.Bar(
            y=top_mae.index,
            x=top_mae.values,
            orientation='h',
            marker_color=['#6c5ce7', '#00b894', '#fd79a8', '#fdcb6e', '#e17055',
                          '#74b9ff', '#a29bfe', '#55efc4'][:len(top_mae)],
            text=[f'{fmt_brl(v)}  ({fmt_brl(v/n_meses_reais)}/mês)' for v in top_mae.values],
            textposition='outside',
            textfont_size=12
        )])
        fig_top.update_layout(height=400, margin=dict(t=10, r=120), xaxis_visible=False, showlegend=False)
        st.plotly_chart(fig_top, use_container_width=True)

    # ---- PROJEÇÃO DOS PRÓXIMOS MESES ----
    st.markdown("---")
    st.markdown("### 🔮 Projeção dos Próximos Meses")

    todos_meses_reais = sorted([m for m in df['Ano_Mes'].unique() if m < '2026-04'])
    ultimos_6m_det = todos_meses_reais[-6:] if len(todos_meses_reais) >= 6 else todos_meses_reais
    df_base_det = df[df['Ano_Mes'].isin(ultimos_6m_det)]

    rec_media_det = df_base_det[df_base_det['Tipo'] == 'INCOME'].groupby('Ano_Mes')['Valor_num'].sum().mean()
    desp_media_det = df_base_det[df_base_det['Tipo'] == 'EXPENSE'].groupby('Ano_Mes')['Valor_num'].sum().mean()

    meses_proj_det = [
        ('Abr/26', True, True), ('Mai/26', True, True), ('Jun/26', True, True),
        ('Jul/26', False, False), ('Ago/26', False, False), ('Set/26', False, False)
    ]

    dados_proj_det = []
    for mes, tem_parcela, tem_protesto in meses_proj_det:
        rec = rec_media_det * 0.95
        desp = desp_media_det
        if tem_parcela:
            desp += 2805
        if tem_protesto:
            desp += 2000
        saldo = rec - desp
        dados_proj_det.append({
            'Mês': mes, 'Entra': fmt_brl(rec), 'Sai': fmt_brl(desp),
            'Sobra': fmt_brl(saldo),
            'Parcela Viagem': 'Sim' if tem_parcela else 'Acabou ✅',
            'Protesto': 'R$ 2.000' if tem_protesto else 'Quitado ✅'
        })

    st.dataframe(pd.DataFrame(dados_proj_det), use_container_width=True, hide_index=True)

    st.markdown("#### 🎯 Datas importantes")
    st.success("✅ **Julho/2026** — Parcelas da viagem acabam! Alívio de R$ 2.805/mês")
    st.success("✅ **Junho/2026** — Protestos quitados se pagar R$ 2.000/mês")
    st.info("💡 **A partir de Julho** — Sem parcelas e sem protestos, sobra mais pra reserva!")


# ============================================================
# PAGINA 4 - ALERTAS
# ============================================================
elif pagina == "alertas":
    # ---- PROJEÇÃO RESUMO (tabela + datas) ----
    st.markdown("### 🔮 Projeção dos Próximos Meses")

    # Calcular bases usando dados REAIS (sem projeção)
    todos_meses_reais = sorted([m for m in df['Ano_Mes'].unique() if m < '2026-04'])
    ultimos_6m = todos_meses_reais[-6:] if len(todos_meses_reais) >= 6 else todos_meses_reais
    df_base = df[df['Ano_Mes'].isin(ultimos_6m)]

    rec_media = df_base[df_base['Tipo'] == 'INCOME'].groupby('Ano_Mes')['Valor_num'].sum().mean()
    desp_media = df_base[df_base['Tipo'] == 'EXPENSE'].groupby('Ano_Mes')['Valor_num'].sum().mean()

    parcelas_viagem = 2805
    protesto_mensal = 2000

    meses_proj = [
        ('Abr/26', True, True), ('Mai/26', True, True), ('Jun/26', True, True),
        ('Jul/26', False, False), ('Ago/26', False, False), ('Set/26', False, False)
    ]

    dados_proj = []
    for mes, tem_parcela, tem_protesto in meses_proj:
        rec = rec_media * 0.95
        desp = desp_media
        if tem_parcela:
            desp += parcelas_viagem
        if tem_protesto:
            desp += protesto_mensal
        saldo = rec - desp
        dados_proj.append({
            'Mês': mes,
            'Entra': fmt_brl(rec),
            'Sai': fmt_brl(desp),
            'Sobra': fmt_brl(saldo),
            'Parcela Viagem': 'Sim' if tem_parcela else 'Acabou ✅',
            'Protesto': f'R$ {protesto_mensal:,.0f}'.replace(',','.') if tem_protesto else 'Quitado ✅'
        })

    st.dataframe(pd.DataFrame(dados_proj), use_container_width=True, hide_index=True)

    st.markdown("#### 🎯 Datas importantes")
    st.success("✅ **Julho/2026** — Parcelas da viagem acabam! Alívio de R$ 2.805/mês")
    st.success("✅ **Junho/2026** — Protestos quitados se pagar R$ 2.000/mês")
    st.info("💡 **A partir de Julho** — Sem parcelas e sem protestos, sobra mais pra reserva!")

    st.markdown("---")

    st.markdown("### ⚠️ Pontos de Atenção")

    # Meses negativos
    resumo = df.groupby(['Ano_Mes', 'Tipo'])['Valor_num'].sum().unstack(fill_value=0)
    if 'INCOME' not in resumo.columns:
        resumo['INCOME'] = 0
    if 'EXPENSE' not in resumo.columns:
        resumo['EXPENSE'] = 0
    resumo['Saldo'] = resumo['INCOME'] - resumo['EXPENSE']

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔴 Meses que gastou mais do que recebeu")
        tem_negativo = False
        for mes, row in resumo.iterrows():
            if row['Saldo'] < 0:
                tem_negativo = True
                st.error(f"**{mes_label_pt(mes)}**: gastou {fmt_brl(abs(row['Saldo']))} a mais")
        if not tem_negativo:
            st.success("Nenhum mês negativo! 🎉")

    with col2:
        st.markdown("#### 🏆 Seus maiores gastos (período todo)")
        desp_all = df[df['Tipo'] == 'EXPENSE']
        top_cats = desp_all.groupby('Categoria')['Valor_num'].sum().sort_values(ascending=False).head(5)
        for i, (cat, val) in enumerate(top_cats.items()):
            emoji = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'][i]
            n_meses_total = df['Ano_Mes'].nunique()
            media = val / n_meses_total
            st.warning(f"{emoji} **{cat}**: {fmt_brl(val)} total ({fmt_brl(media)}/mês)")

    st.markdown("---")

    st.markdown("#### 💡 Onde você pode economizar (metas da nossa sessão)")
    col1, col2, col3 = st.columns(3)

    n_meses_total = df['Ano_Mes'].nunique()

    with col1:
        compras_mes = desp_all[desp_all['Categoria'].isin(['Compras Geral', 'Alimentação', 'Mercado'])]\
            ['Valor_num'].sum() / n_meses_total
        st.metric("🛒 Compras/Alimentação", f"{fmt_brl(compras_mes)}/mês",
                  f"Meta: R$ 4.000 (economia de {fmt_brl(max(0, compras_mes - 4000))})",
                  delta_color="inverse")

    with col2:
        cuidados_mes = desp_all[desp_all['Categoria'].isin(['Cuidados pessoais Geral', 'Academia', 'Beleza / Estética'])]\
            ['Valor_num'].sum() / n_meses_total
        st.metric("💅 Cuidados Pessoais", f"{fmt_brl(cuidados_mes)}/mês",
                  f"Meta: R$ 5.000 (economia de {fmt_brl(max(0, cuidados_mes - 5000))})",
                  delta_color="inverse")

    with col3:
        economia_total = max(0, compras_mes - 4000) + max(0, cuidados_mes - 5000)
        st.metric("💰 Economia Potencial", f"{fmt_brl(economia_total)}/mês",
                  f"{fmt_brl(economia_total * 12)}/ano")

    st.markdown("---")

    st.markdown("#### 📌 Seus compromissos")
    st.markdown("""
    | O quê | Quanto | Até quando | Situação |
    |-------|--------|------------|----------|
    | Protestos cartório | R$ 2.000/mês | Junho/2026 | 🔴 Pagar |
    | Parcelas viagem Londres | R$ 2.805/mês | Julho/2026 | 🟡 Pagando |
    | Advogada FIES | R$ 1.500 + R$ 1.500 | Após viagem | 🟡 Iniciado |
    | Simples Nacional | R$ 354/mês | Parcelado | 🟢 Em dia |
    | Seguro RC (médico) | ~R$ 100/mês | Contratar | ⚪ Pendente |
    | Poupança automática XP | R$ 2.000/mês | Todo mês | ⚪ Configurar |
    """)

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #b2bec3; font-size: 0.8rem; padding: 10px;'>"
    "💜 Dashboard Financeiro · GW9 Capital · Assessoria Personalizada"
    "</div>",
    unsafe_allow_html=True
)
