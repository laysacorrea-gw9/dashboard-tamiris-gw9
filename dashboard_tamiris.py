import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Finanças - Dra. Tamiris",
    page_icon=":material/account_balance_wallet:",
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


# CSS global
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body { font-family: 'Inter', sans-serif !important; }
    .main .block-container { padding-top: 1.5rem; max-width: 1400px; }
    /* Labels de widgets */
    .stSelectbox > label, .stMultiSelect > label,
    .stRadio > label, .stSlider > label { font-size: 14px; font-weight: 600; }
    /* Texto geral do sidebar */
    section[data-testid="stSidebar"] { font-size: 14px; }
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
@st.cache_data(ttl=30)
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

    media_por_cat = df_base[df_base['Tipo'] == 'EXPENSE'].groupby('Categoria')['Valor_num'].sum() / n
    media_rec_cat = df_base[df_base['Tipo'] == 'INCOME'].groupby('Categoria')['Valor_num'].sum() / n

    meses_futuros = ['2026-04', '2026-05', '2026-06', '2026-07', '2026-08', '2026-09']
    parcelas_viagem = 2805
    protesto_mensal = 2000

    rows = []
    for mes in meses_futuros:
        tem_parcela = mes <= '2026-06'

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
        for col in df.columns:
            if col not in df_proj.columns:
                df_proj[col] = ''
        df = pd.concat([df, df_proj[df.columns]], ignore_index=True)

    return df


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.image("https://gw9capital.com.br/wp-content/uploads/2024/03/LOGO-BRANCA.png", width=160)

    st.markdown("### :material/person: Dra. Tamiris Paiva")
    st.caption("Médica · 35 anos")
    st.caption(":material/support_agent: Assessora: Laysa Corrêa")

    st.markdown("---")

    if 'pagina' not in st.session_state:
        st.session_state.pagina = "mes"

    menu_items = [
        ("mes", ":material/calendar_month: Mês a mês"),
        ("detalhe", ":material/query_stats: Projeção Anual"),
        ("alertas", ":material/notifications: Alertas"),
    ]

    for key, label in menu_items:
        is_active = st.session_state.pagina == key
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
            st.session_state.pagina = key
            st.rerun()

    pagina = st.session_state.pagina

    st.markdown("---")

    default_csv = os.path.join(os.path.dirname(__file__), "Planfi", "Planfi - set.2025 a 03.2026.csv")
    uploaded = st.file_uploader(":material/upload_file: Carregar novo CSV", type=['csv'])

    if uploaded:
        df = load_data(uploaded_file=uploaded)
    else:
        df = load_data(file_path=default_csv)

    if df is None:
        st.error("Nenhum CSV encontrado.", icon=":material/error:")
        st.stop()

# ============================================================
# HEADER
# ============================================================
st.title(":material/account_balance_wallet: Suas finanças, Tamiris")

# Função de card colorido — usada em múltiplas páginas
def card_html(bg, shadow, icon, label, value, extra=""):
    return f"""
    <div style="background:{bg}; border-radius:18px; padding:22px 24px;
         box-shadow:0 8px 24px {shadow}; color:white; margin-bottom:6px;
         min-height:180px; box-sizing:border-box;
         display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;">
      <div style="display:flex; align-items:center; gap:14px; justify-content:center;">
        <div style="background:rgba(255,255,255,0.25); border-radius:50%;
             width:56px; height:56px; display:flex; align-items:center;
             justify-content:center; font-size:1.6rem; flex-shrink:0;">{icon}</div>
        <div>
          <div style="font-size:1.15rem; opacity:0.88; font-weight:600;">{label}</div>
          <div style="font-size:2.4rem; font-weight:800; line-height:1.1;">{value}</div>
        </div>
      </div>
      {extra}
    </div>"""

meses_disponiveis = sorted(df['Ano_Mes'].unique())

# ============================================================
# SELETOR DE MES (só na página Mês a Mês) e CARDS DE RESUMO
# ============================================================
if pagina == "mes":
    if 'idx_mes' not in st.session_state:
        mes_atual = datetime.now().strftime('%Y-%m')
        if mes_atual in meses_disponiveis:
            st.session_state.idx_mes = meses_disponiveis.index(mes_atual)
        else:
            meses_reais = [m for m in meses_disponiveis if m <= mes_atual]
            st.session_state.idx_mes = meses_disponiveis.index(meses_reais[-1]) if meses_reais else len(meses_disponiveis) - 1

    # Navegação de mês com seta
    col_espL, col_esq, col_mes_sel, col_dir, col_espR = st.columns([2, 0.3, 1.5, 0.3, 2])
    with col_esq:
        if st.button("◁", key="btn_esq", help="Mês anterior"):
            if st.session_state.idx_mes > 0:
                st.session_state.idx_mes -= 1
                st.rerun()
    with col_mes_sel:
        st.markdown(
            f"<div style='text-align:center; font-size:1.1rem; font-weight:600; "
            f"padding:6px 16px; border:1.5px solid #b2bec3; "
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
        st.info(
            "**Projeção** — valores estimados baseados no padrão de consumo (Set/25 a Fev/26)",
            icon=":material/auto_graph:"
        )

    desp_fixas_mes = despesas_mes[despesas_mes['Categoria'].isin(CATEGORIAS_FIXAS)]['Valor_num'].sum()
    desp_var_mes = despesas_mes[despesas_mes['Categoria'].isin(CATEGORIAS_VARIAVEIS)]['Valor_num'].sum()
    desp_outros_mes = saiu - desp_fixas_mes - desp_var_mes

    # Cards de resumo do mês — estilo flat com ícone
    bal_bg     = "#00b894" if saldo_mes >= 0 else "#d63031"
    bal_shadow = "rgba(0,184,148,0.35)" if saldo_mes >= 0 else "rgba(214,48,49,0.35)"
    bal_label  = "Sobrou" if saldo_mes >= 0 else "Faltou"
    bal_icon   = "↑" if saldo_mes >= 0 else "↓"


    sub_fixos = f"""
        <div style="display:flex; gap:10px; margin-top:14px; width:100%;">
          <div style="flex:1; background:rgba(255,255,255,0.18); border-radius:12px; padding:16px 10px; text-align:center;">
            <div style="font-size:1rem; opacity:0.9; margin-bottom:6px; font-weight:600;">🔒 Fixos</div>
            <div style="font-size:1.4rem; font-weight:800;">{fmt_brl(desp_fixas_mes)}</div>
          </div>
          <div style="flex:1; background:rgba(255,255,255,0.18); border-radius:12px; padding:16px 10px; text-align:center;">
            <div style="font-size:1rem; opacity:0.9; margin-bottom:6px; font-weight:600;">🔄 Variáveis</div>
            <div style="font-size:1.4rem; font-weight:800;">{fmt_brl(desp_var_mes)}</div>
          </div>
          <div style="flex:1; background:rgba(255,255,255,0.18); border-radius:12px; padding:16px 10px; text-align:center;">
            <div style="font-size:1rem; opacity:0.9; margin-bottom:6px; font-weight:600;">📦 Outros</div>
            <div style="font-size:1.4rem; font-weight:800;">{fmt_brl(desp_outros_mes)}</div>
          </div>
        </div>"""

    col_e, col_s, col_b = st.columns([1, 1.4, 1])

    with col_e:
        st.markdown(card_html("#00b894", "rgba(0,184,148,0.35)", "↑", "Entradas", fmt_brl(entrou)), unsafe_allow_html=True)

    with col_s:
        st.markdown(f"""
        <div style="background:#e17055; border-radius:18px; padding:22px 24px;
             box-shadow:0 8px 24px rgba(225,112,85,0.35); color:white; margin-bottom:6px;
             min-height:180px; box-sizing:border-box;
             display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;">
          <div style="display:flex; align-items:center; gap:14px; justify-content:center;">
            <div style="background:rgba(255,255,255,0.25); border-radius:50%;
                 width:56px; height:56px; display:flex; align-items:center;
                 justify-content:center; font-size:1.6rem; flex-shrink:0;">↓</div>
            <div>
              <div style="font-size:1.15rem; opacity:0.88; font-weight:600;">Saídas</div>
              <div style="font-size:2.4rem; font-weight:800; line-height:1.1;">{fmt_brl(saiu)}</div>
            </div>
          </div>
          <div style="display:flex; gap:10px; margin-top:14px; width:100%;">
            <div style="flex:1; background:rgba(255,255,255,0.18); border-radius:12px; padding:16px 10px; text-align:center;">
              <div style="font-size:1rem; opacity:0.9; margin-bottom:6px; font-weight:600;">🔒 Fixos</div>
              <div style="font-size:1.4rem; font-weight:800;">{fmt_brl(desp_fixas_mes)}</div>
            </div>
            <div style="flex:1; background:rgba(255,255,255,0.18); border-radius:12px; padding:16px 10px; text-align:center;">
              <div style="font-size:1rem; opacity:0.9; margin-bottom:6px; font-weight:600;">🔄 Variáveis</div>
              <div style="font-size:1.4rem; font-weight:800;">{fmt_brl(desp_var_mes)}</div>
            </div>
            <div style="flex:1; background:rgba(255,255,255,0.18); border-radius:12px; padding:16px 10px; text-align:center;">
              <div style="font-size:1rem; opacity:0.9; margin-bottom:6px; font-weight:600;">📦 Outros</div>
              <div style="font-size:1.4rem; font-weight:800;">{fmt_brl(desp_outros_mes)}</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

    with col_b:
        st.markdown(card_html(bal_bg, bal_shadow, bal_icon, bal_label, fmt_brl(abs(saldo_mes))), unsafe_allow_html=True)

elif pagina == "detalhe":
    periodo_txt = f"{mes_label_curto(meses_disponiveis[0])} a {mes_label_curto(meses_disponiveis[-1])}"
    st.caption(f":material/date_range: Período: {periodo_txt} · {len(df):,} transações")

    total_receita = df[df['Tipo'] == 'INCOME']['Valor_num'].sum()
    total_despesa = df[df['Tipo'] == 'EXPENSE']['Valor_num'].sum()
    balanco_total = total_receita - total_despesa
    pp = balanco_total / max(total_receita, 1) * 100

    bal_bg_d     = "#00b894" if balanco_total >= 0 else "#d63031"
    bal_shadow_d = "rgba(0,184,148,0.35)" if balanco_total >= 0 else "rgba(214,48,49,0.35)"
    bal_icon_d   = "↑" if balanco_total >= 0 else "↓"
    bal_label_d  = "Balanço +" if balanco_total >= 0 else "Balanço"
    pp_bg        = "#00b894" if pp >= 0 else "#d63031"
    pp_shadow    = "rgba(0,184,148,0.35)" if pp >= 0 else "rgba(214,48,49,0.35)"

    cd1, cd2, cd3, cd4 = st.columns(4)
    with cd1:
        st.markdown(card_html("#00b894", "rgba(0,184,148,0.35)", "↑", "Receita Total", fmt_brl(total_receita)), unsafe_allow_html=True)
    with cd2:
        st.markdown(card_html("#e17055", "rgba(225,112,85,0.35)", "↓", "Despesa Total", fmt_brl(total_despesa)), unsafe_allow_html=True)
    with cd3:
        st.markdown(card_html(bal_bg_d, bal_shadow_d, bal_icon_d, bal_label_d, fmt_brl(abs(balanco_total))), unsafe_allow_html=True)
    with cd4:
        st.markdown(card_html(pp_bg, pp_shadow, "%", "Taxa de Poupança", f"{pp:.1f}%"), unsafe_allow_html=True)

# ============================================================
# PAGINAS (baseado na sidebar)
# ============================================================
if pagina == "mes":
    # Alerta sem categoria
    sem_cat = df_mes[df_mes['Categoria'] == 'Sem Categoria']
    if len(sem_cat) > 0:
        total_sem_cat = sem_cat['Valor_num'].sum()
        st.markdown(
            f"""<div style="background:#FFD600; color:#1a1a1a; border-radius:12px;
            padding:14px 20px; font-size:1rem; font-weight:700;
            border-left:6px solid #e6c000; margin-bottom:10px;">
            ⚠️ {len(sem_cat)} transações sem categoria ({fmt_brl(total_sem_cat)}) — categorize no Planfi!
            </div>""",
            unsafe_allow_html=True
        )

    if 'filtro_cat_pizza' not in st.session_state:
        st.session_state.filtro_cat_pizza = None

    col_desp, col_rec = st.columns(2)

    with col_desp:
        with st.container(border=True):
            st.subheader(":material/pie_chart: Pra onde foi seu dinheiro")

            desp_cat = despesas_mes.groupby('Categoria_Mae')['Valor_num'].sum().sort_values(ascending=False)
            desp_cat = desp_cat.rename(index={'Sem Categoria': '⚠️ Sem Categoria'})
            total_desp = desp_cat.sum()

            if total_desp > 0:
                desp_pct = desp_cat / total_desp * 100
                principais = desp_pct[desp_pct >= 3]
                outros = desp_pct[desp_pct < 3]

                valores_pizza = list(desp_cat[principais.index].values)
                nomes_pizza = list(principais.index)

                if len(outros) > 0:
                    valores_pizza.append(desp_cat[outros.index].sum())
                    nomes_pizza.append(f'Outros ({len(outros)} categorias)')

                cores = ['#7c5cbf', '#00b894', '#fd79a8', '#fdcb6e', '#e17055',
                         '#74b9ff', '#a29bfe', '#55efc4', '#fab1a0', '#00cec9',
                         '#b2bec3', '#636e72', '#e84393', '#0984e3', '#dfe6e9']

                cores_pizza = []
                pull_pizza = []
                for i, nome in enumerate(nomes_pizza):
                    if '⚠️ Sem Categoria' in nome:
                        cores_pizza.append('#FFD600')
                        pull_pizza.append(0.12)
                    else:
                        cores_pizza.append(cores[i % len(cores)])
                        pull_pizza.append(0)

                # Textos customizados: "Nome\nX%" fora, hover mostra R$
                textos_externos = [
                    f"<b>{nome}</b><br>{desp_cat[principais.index].get(nome, desp_cat.get(nome, 0)) / total_desp * 100:.1f}%"
                    if nome in desp_cat.index
                    else f"<b>{nome}</b><br>{sum(desp_cat[outros.index].values) / total_desp * 100:.1f}%"
                    for nome in nomes_pizza
                ]

                fig_pizza = go.Figure()

                # Trace 1: fatias coloridas — nome + R$ do lado de FORA
                fig_pizza.add_trace(go.Pie(
                    labels=nomes_pizza,
                    values=valores_pizza,
                    hole=0.42,
                    texttemplate='<b>%{label}</b><br><b>%{customdata}</b>',
                    textposition='outside',
                    textfont=dict(size=14, color='#2d3436'),
                    marker=dict(colors=cores_pizza, line=dict(width=2, color='white')),
                    pull=pull_pizza,
                    customdata=[fmt_brl(v) for v in valores_pizza],
                    hovertemplate='<b>%{label}</b><br>%{percent:.1%}<br>%{customdata}<extra></extra>',
                    showlegend=False,
                ))

                # Trace 2: overlay transparente — só % DENTRO de cada fatia
                fig_pizza.add_trace(go.Pie(
                    labels=nomes_pizza,
                    values=valores_pizza,
                    hole=0.42,
                    texttemplate='<b>%{percent:.1%}</b>',
                    textposition='inside',
                    textfont=dict(size=13, color='#2d3436'),
                    marker=dict(
                        colors=['rgba(0,0,0,0)'] * len(nomes_pizza),
                        line=dict(width=0, color='rgba(0,0,0,0)')
                    ),
                    hoverinfo='skip',
                    showlegend=False,
                ))

                fig_pizza.update_layout(
                    height=580,
                    margin=dict(t=90, b=90, l=120, r=120),
                    showlegend=False,
                    annotations=[dict(
                        text=f'<b>{fmt_brl(total_desp)}</b>',
                        x=0.5, y=0.5, font_size=16, showarrow=False
                    )],
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                )

                evento = st.plotly_chart(
                    fig_pizza, use_container_width=True,
                    on_select="rerun", key="pizza_click"
                )

                if evento and evento.selection and evento.selection.points:
                    cat_clicada = evento.selection.points[0].get('label', None)
                    if cat_clicada:
                        if cat_clicada == st.session_state.filtro_cat_pizza:
                            st.session_state.filtro_cat_pizza = None
                        else:
                            st.session_state.filtro_cat_pizza = cat_clicada
                        st.rerun()

                if st.session_state.filtro_cat_pizza:
                    st.badge(
                        f"Filtrado: {st.session_state.filtro_cat_pizza}",
                        icon=":material/filter_alt:",
                        color="violet"
                    )
                    if st.button("Limpar filtro", key="limpar_pizza"):
                        st.session_state.filtro_cat_pizza = None
                        st.rerun()
            else:
                st.caption("Sem despesas neste mês")

    with col_rec:
        with st.container(border=True):
            st.subheader(":material/payments: De onde veio seu dinheiro")

            rec_cat = receitas_mes.groupby('Categoria')['Valor_num'].sum().sort_values(ascending=True)

            if len(rec_cat) > 0:
                cores_rec = ['#00b894', '#55efc4', '#81ecec', '#74b9ff',
                             '#a29bfe', '#7c5cbf', '#dfe6e9', '#b2bec3',
                             '#fdcb6e', '#fab1a0', '#e17055']

                total_rec = rec_cat.sum()
                # Labels iguais à pizza: Nome em negrito + % abaixo
                tick_labels = [f"<b>{cat}</b><br>{v/total_rec*100:.1f}%" for cat, v in zip(rec_cat.index, rec_cat.values)]

                fig_rec = go.Figure(data=[go.Bar(
                    y=tick_labels,
                    x=rec_cat.values,
                    orientation='h',
                    marker_color=cores_rec[:len(rec_cat)],
                    text=[f"<b>{fmt_brl(v)}</b>" for v in rec_cat.values],
                    textposition='outside',
                    textfont=dict(size=13, color='#2d3436'),
                    hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>',
                    customdata=[[cat, fmt_brl(v)] for cat, v in zip(rec_cat.index, rec_cat.values)],
                )])

                max_val = rec_cat.max()
                fig_rec.update_layout(
                    height=420,
                    margin=dict(t=10, b=20, l=10, r=120),
                    xaxis_title="",
                    yaxis_title="",
                    showlegend=False,
                    xaxis=dict(range=[0, max_val * 1.4], visible=False),
                    yaxis=dict(tickfont=dict(size=13, color='#2d3436')),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig_rec, use_container_width=True)
            else:
                st.caption("Sem receitas neste mês")

    # TABELA DE LANÇAMENTOS DO MÊS
    st.subheader(f":material/receipt_long: Lançamentos de {mes_label_pt(mes_selecionado)}")

    df_tabela_mes = df_mes[['Data', 'Tipo', 'Valor_num', 'Descrição', 'Categoria', 'Categoria_Mae', 'Conta']].copy()
    df_tabela_mes['Tipo_label'] = df_tabela_mes['Tipo'].map({'INCOME': 'Entrada', 'EXPENSE': 'Saída'})

    # Filtros inline
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        tipos_opcoes = ["Todos", "Entrada", "Saída"]
        filtro_tipo = st.selectbox("Tipo:", tipos_opcoes, key="filtro_tipo_mes")
    with fc2:
        cats_disponiveis = sorted(df_tabela_mes['Categoria_Mae'].unique())
        # Se a pizza está filtrada, pré-selecionar a categoria clicada
        default_cat = []
        if st.session_state.filtro_cat_pizza and st.session_state.filtro_cat_pizza in cats_disponiveis:
            default_cat = [st.session_state.filtro_cat_pizza]
        filtro_cat = st.multiselect("Categoria:", cats_disponiveis, default=default_cat, key="filtro_cat_col")
    with fc3:
        contas_mes = sorted(df_tabela_mes['Conta'].unique())
        filtro_conta = st.multiselect("Conta:", contas_mes, key="filtro_conta_mes")
    with fc4:
        busca_desc = st.text_input("Buscar na descrição:", key="busca_desc_mes", placeholder="Digite para filtrar...")

    # Aplicar filtros
    df_show = df_tabela_mes.copy()
    if filtro_tipo == "Entrada":
        df_show = df_show[df_show['Tipo'] == 'INCOME']
    elif filtro_tipo == "Saída":
        df_show = df_show[df_show['Tipo'] == 'EXPENSE']
    if filtro_cat:
        df_show = df_show[df_show['Categoria_Mae'].isin(filtro_cat)]
    if filtro_conta:
        df_show = df_show[df_show['Conta'].isin(filtro_conta)]
    if busca_desc:
        df_show = df_show[df_show['Descrição'].str.contains(busca_desc, case=False, na=False)]

    total_filtrado = df_show['Valor_num'].sum()
    filtros_ativos = []
    if filtro_tipo != "Todos":
        filtros_ativos.append(filtro_tipo)
    if filtro_cat:
        filtros_ativos.append(', '.join(filtro_cat))
    if filtro_conta:
        filtros_ativos.append(', '.join(filtro_conta))
    filtro_txt = f" · Filtro: **{' | '.join(filtros_ativos)}**" if filtros_ativos else ""
    st.caption(f"{len(df_show)} lançamentos · Total: **{fmt_brl(total_filtrado)}**{filtro_txt}")

    df_display = df_show[['Data', 'Tipo_label', 'Valor_num', 'Descrição', 'Categoria', 'Conta']]\
        .sort_values('Data', ascending=False)

    st.dataframe(
        df_display,
        use_container_width=True,
        height=420,
        hide_index=True,
        column_config={
            "Data": st.column_config.TextColumn("Data", width="small"),
            "Tipo_label": st.column_config.TextColumn("Tipo", width="small"),
            "Valor_num": st.column_config.NumberColumn(
                "Valor",
                format="R$ %.2f",
                width="medium",
            ),
            "Descrição": st.column_config.TextColumn("Descrição", width="large"),
            "Categoria": st.column_config.TextColumn("Categoria", width="medium"),
            "Conta": st.column_config.TextColumn("Conta", width="medium"),
        }
    )


# ============================================================
# PAGINA 2 - DETALHAMENTO (VISÃO DO ANO)
# ============================================================
elif pagina == "detalhe":
    st.subheader(":material/query_stats: Visão do ano")

    # Filtro de meses
    todos_meses_labels = [mes_label_curto(m) for m in meses_disponiveis]
    f1, f2 = st.columns(2)
    with f1:
        mes_ini_label = st.selectbox("De:", todos_meses_labels, index=0, key="detalhe_ini")
    with f2:
        mes_fim_label = st.selectbox("Até:", todos_meses_labels, index=len(todos_meses_labels)-1, key="detalhe_fim")

    idx_ini = todos_meses_labels.index(mes_ini_label)
    idx_fim = todos_meses_labels.index(mes_fim_label)
    if idx_ini > idx_fim:
        idx_ini, idx_fim = idx_fim, idx_ini
    meses_filtrados = meses_disponiveis[idx_ini:idx_fim+1]
    df_detalhe = df[df['Ano_Mes'].isin(meses_filtrados)]

    st.markdown("---")

    # Histórico mensal de saldo
    st.markdown("**Sobrou ou faltou em cada mês?**")

    resumo_mensal = df_detalhe.groupby(['Ano_Mes', 'Tipo'])['Valor_num'].sum().unstack(fill_value=0)
    if 'INCOME' not in resumo_mensal.columns:
        resumo_mensal['INCOME'] = 0
    if 'EXPENSE' not in resumo_mensal.columns:
        resumo_mensal['EXPENSE'] = 0
    resumo_mensal['Saldo'] = resumo_mensal['INCOME'] - resumo_mensal['EXPENSE']
    resumo_mensal = resumo_mensal.sort_index()

    meses_hist = resumo_mensal.index.tolist()
    meses_hist_label = [mes_label_curto(m) for m in meses_hist]
    cores_saldo = ['#00b894' if v >= 0 else '#e17055' for v in resumo_mensal['Saldo']]

    with st.container(border=True):
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Bar(
            x=meses_hist_label,
            y=resumo_mensal['Saldo'],
            marker_color=cores_saldo,
            text=[f'<b>{fmt_brl(v)}</b>' for v in resumo_mensal['Saldo']],
            textposition='outside',
            textfont=dict(size=14, color='#2d3436'),
            hovertemplate='<b>%{x}</b><br>%{customdata}<extra></extra>',
            customdata=[fmt_brl(v) for v in resumo_mensal['Saldo']],
        ))
        fig_hist.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        # Linha vertical separando passado do futuro
        mes_corte = '2026-03'
        if mes_corte in meses_hist:
            idx_corte = meses_hist.index(mes_corte)
            x_corte = idx_corte + 0.5  # entre o último mês real e o primeiro projetado

            fig_hist.add_vline(
                x=x_corte, line_dash="dot", line_color="#6c5ce7", line_width=2, opacity=0.8
            )
            y_max = resumo_mensal['Saldo'].abs().max() * 0.85

            # Label PASSADO (esquerda)
            fig_hist.add_annotation(
                x=x_corte - 0.6, y=y_max,
                text="◀ <b>Passado</b>",
                showarrow=False,
                font=dict(size=16, color="#6c5ce7"),
                xanchor="right"
            )
            # Label FUTURO (direita)
            fig_hist.add_annotation(
                x=x_corte + 0.6, y=y_max,
                text="<b>Futuro</b> ▶",
                showarrow=False,
                font=dict(size=16, color="#6c5ce7"),
                xanchor="left"
            )

        fig_hist.update_layout(
            height=340,
            margin=dict(t=30, b=20),
            yaxis_visible=False,
            showlegend=False,
            xaxis=dict(title="", tickfont=dict(size=13, color='#2d3436')),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        st.markdown("<span style='color:#00b894; font-size:13px; font-weight:700;'>● Verde</span> <span style='font-size:13px;'> = sobrou &nbsp;&nbsp;</span><span style='color:#e17055; font-size:13px; font-weight:700;'>● Vermelho</span><span style='font-size:13px;'> = gastou mais do que recebeu &nbsp;&nbsp;</span><span style='color:#6c5ce7; font-size:13px; font-weight:700;'>┆ Linha roxa</span><span style='font-size:13px;'> = divide passado e futuro</span>", unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader(":material/lock: Gastos fixos vs variáveis")
        desp_all = df_detalhe[df_detalhe['Tipo'] == 'EXPENSE']
        desp_tipo = desp_all.groupby(['Ano_Mes', 'Tipo_Despesa'])['Valor_num'].sum().reset_index()
        desp_tipo['Mês'] = desp_tipo['Ano_Mes'].apply(mes_label_curto)

        # Cores mais harmoniosas e legíveis
        COR_FIXA     = '#5c6bc0'   # azul índigo
        COR_VARIAVEL = '#ef6c00'   # laranja queimado
        COR_OUTROS   = '#ffd54f'   # amarelo suave

        meses_ord = desp_tipo['Mês'].unique().tolist()
        tipos = ['Fixa', 'Variável', 'Outros']
        cores_map = {'Fixa': COR_FIXA, 'Variável': COR_VARIAVEL, 'Outros': COR_OUTROS}

        fig_fixvar = go.Figure()
        for tipo in tipos:
            d = desp_tipo[desp_tipo['Tipo_Despesa'] == tipo]
            if d.empty:
                continue
            fig_fixvar.add_trace(go.Bar(
                x=d['Mês'], y=d['Valor_num'],
                name=tipo,
                marker_color=cores_map[tipo],
                text=[f'<b>{v/1000:.0f}k</b>' for v in d['Valor_num']],
                textposition='inside',
                insidetextanchor='middle',
                textfont=dict(size=12, color='#2d3436'),
            ))

        fig_fixvar.update_layout(
            barmode='stack',
            height=400, margin=dict(t=10, b=10),
            yaxis=dict(tickformat=",.0f", tickfont=dict(size=12, color='#2d3436')),
            xaxis=dict(tickfont=dict(size=12, color='#2d3436'), categoryorder='array', categoryarray=meses_ord),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, font=dict(size=13)),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_fixvar, use_container_width=True)

    with st.container(border=True):
        st.subheader(":material/leaderboard: Onde você mais gasta (no período)")
        desp_all = df_detalhe[df_detalhe['Tipo'] == 'EXPENSE']
        desp_reais = desp_all[desp_all['Ano_Mes'] < '2026-04']
        n_meses_reais = max(desp_reais['Ano_Mes'].nunique(), 1)
        top_mae = desp_reais.groupby('Categoria_Mae')['Valor_num'].sum().sort_values(ascending=True).tail(8)

        fig_top = go.Figure(data=[go.Bar(
            y=top_mae.index,
            x=top_mae.values,
            orientation='h',
            marker_color=['#7c5cbf', '#00b894', '#fd79a8', '#fdcb6e', '#e17055',
                          '#74b9ff', '#a29bfe', '#55efc4'][:len(top_mae)],
            text=[f'<b>{fmt_brl(v)}</b>  ({fmt_brl(v/n_meses_reais)}/mês)' for v in top_mae.values],
            textposition='outside',
            textfont=dict(size=13, color='#2d3436'),
            hovertemplate='<b>%{y}</b><br>Total: %{customdata}<extra></extra>',
            customdata=[fmt_brl(v) for v in top_mae.values],
        )])
        fig_top.update_layout(
            height=360, margin=dict(t=10, r=10, l=10),
            xaxis=dict(visible=False, range=[0, top_mae.max() * 1.55]),
            yaxis=dict(tickfont=dict(size=13, color='#2d3436')),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_top, use_container_width=True)

    # Projeção dos próximos meses
    st.subheader(":material/auto_graph: Projeção dos próximos meses")

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
            'Mês': mes, 'Entra': rec, 'Sai': desp,
            'Sobra': saldo,
            'Parcela viagem': 'Sim' if tem_parcela else 'Acabou',
            'Protesto': 'R$ 2.000' if tem_protesto else 'Quitado'
        })

    df_proj_det = pd.DataFrame(dados_proj_det)

    st.dataframe(
        df_proj_det,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Mês": st.column_config.TextColumn("Mês", width="small"),
            "Entra": st.column_config.NumberColumn("Entra", format="R$ %.0f"),
            "Sai": st.column_config.NumberColumn("Sai", format="R$ %.0f"),
            "Sobra": st.column_config.NumberColumn("Sobra", format="R$ %.0f"),
            "Parcela viagem": st.column_config.TextColumn("Parcela viagem", width="small"),
            "Protesto": st.column_config.TextColumn("Protesto", width="small"),
        }
    )

    st.markdown("**Datas importantes**")
    st.success("**Julho/2026** — Parcelas da viagem acabam! Alívio de R$ 2.805/mês", icon=":material/check_circle:")
    st.success("**Junho/2026** — Protestos quitados se pagar R$ 2.000/mês", icon=":material/check_circle:")
    st.info("**A partir de julho** — Sem parcelas e sem protestos, sobra mais pra reserva!", icon=":material/lightbulb:")


# ============================================================
# PAGINA 3 - ALERTAS
# ============================================================
elif pagina == "alertas":
    st.subheader(":material/notifications: Pontos de atenção")

    resumo = df.groupby(['Ano_Mes', 'Tipo'])['Valor_num'].sum().unstack(fill_value=0)
    if 'INCOME' not in resumo.columns:
        resumo['INCOME'] = 0
    if 'EXPENSE' not in resumo.columns:
        resumo['EXPENSE'] = 0
    resumo['Saldo'] = resumo['INCOME'] - resumo['EXPENSE']

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("**Meses que gastou mais do que recebeu**")
            tem_negativo = False
            for mes, row in resumo.iterrows():
                if row['Saldo'] < 0:
                    tem_negativo = True
                    st.error(f"**{mes_label_pt(mes)}**: gastou {fmt_brl(abs(row['Saldo']))} a mais", icon=":material/error:")
            if not tem_negativo:
                st.success("Nenhum mês negativo!", icon=":material/check_circle:")

    with col2:
        with st.container(border=True):
            st.markdown("**Seus maiores gastos (período todo)**")
            desp_all = df[df['Tipo'] == 'EXPENSE']
            top_cats = desp_all.groupby('Categoria')['Valor_num'].sum().sort_values(ascending=False).head(5)
            medals = ['1°', '2°', '3°', '4°', '5°']
            for i, (cat, val) in enumerate(top_cats.items()):
                n_meses_total = df['Ano_Mes'].nunique()
                media = val / n_meses_total
                st.warning(f"**{medals[i]} {cat}**: {fmt_brl(val)} total ({fmt_brl(media)}/mês)", icon=":material/trending_up:")

    st.subheader(":material/savings: Onde você pode economizar")
    st.caption("Metas da nossa sessão de planejamento")

    col1, col2, col3 = st.columns(3)
    n_meses_total = df['Ano_Mes'].nunique()
    desp_all = df[df['Tipo'] == 'EXPENSE']

    with col1:
        compras_mes = desp_all[desp_all['Categoria'].isin(['Compras Geral', 'Alimentação', 'Mercado'])]\
            ['Valor_num'].sum() / n_meses_total
        st.metric(
            "Compras / alimentação", f"{fmt_brl(compras_mes)}/mês",
            f"Meta: R$ 4.000 (economia de {fmt_brl(max(0, compras_mes - 4000))})",
            delta_color="inverse", border=True
        )

    with col2:
        cuidados_mes = desp_all[desp_all['Categoria'].isin(['Cuidados pessoais Geral', 'Academia', 'Beleza / Estética'])]\
            ['Valor_num'].sum() / n_meses_total
        st.metric(
            "Cuidados pessoais", f"{fmt_brl(cuidados_mes)}/mês",
            f"Meta: R$ 5.000 (economia de {fmt_brl(max(0, cuidados_mes - 5000))})",
            delta_color="inverse", border=True
        )

    with col3:
        economia_total = max(0, compras_mes - 4000) + max(0, cuidados_mes - 5000)
        st.metric(
            "Economia potencial", f"{fmt_brl(economia_total)}/mês",
            f"{fmt_brl(economia_total * 12)}/ano",
            border=True
        )

    st.subheader(":material/assignment: Seus compromissos")
    st.dataframe(
        pd.DataFrame([
            {"O quê": "Protestos cartório", "Quanto": "R$ 2.000/mês", "Até quando": "Junho/2026", "Situação": "Pagar"},
            {"O quê": "Parcelas viagem Londres", "Quanto": "R$ 2.805/mês", "Até quando": "Julho/2026", "Situação": "Pagando"},
            {"O quê": "Advogada FIES", "Quanto": "R$ 1.500 + R$ 1.500", "Até quando": "Após viagem", "Situação": "Iniciado"},
            {"O quê": "Simples Nacional", "Quanto": "R$ 354/mês", "Até quando": "Parcelado", "Situação": "Em dia"},
            {"O quê": "Seguro RC (médico)", "Quanto": "~R$ 100/mês", "Até quando": "Contratar", "Situação": "Pendente"},
            {"O quê": "Poupança automática XP", "Quanto": "R$ 2.000/mês", "Até quando": "Todo mês", "Situação": "Configurar"},
        ]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "O quê": st.column_config.TextColumn("O quê", width="medium"),
            "Quanto": st.column_config.TextColumn("Quanto", width="medium"),
            "Até quando": st.column_config.TextColumn("Até quando", width="small"),
            "Situação": st.column_config.TextColumn("Situação", width="small"),
        }
    )

# ============================================================
# FOOTER
# ============================================================
st.caption(":material/favorite: Dashboard financeiro · GW9 Capital · Assessoria personalizada", text_alignment="center")
