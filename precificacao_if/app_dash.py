"""
app_dash.py — Precificação de Crédito IF
Layout: Noir Gold (Dash + Plotly) — inspirado no FinanceOS design
"""
import dash
from dash import dcc, html, Input, Output, State, callback_context, ALL, MATCH
import plotly.graph_objects as go
import pandas as pd
import sys, os, json, copy
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from recipe       import RECEITAS, carregar
from engine_core  import executar
from exporters    import para_excel
from rating_model import (build_tabela, CriteriosViabilidade,
                           taxa_de_pct_cdi, pct_cdi_de_taxa,
                           RATINGS_ORDEM, CORES_RATING, PD_DEFAULTS_AA, LGD_DEFAULT)
from portfolio_sim import simular_portfolio, simular_portfolio_v2, _clone_direto
from funding_faixas import FAIXAS_PADRAO, wacc_faixas, taxa_am_de_aa, taxa_total_faixa

# ── APP ───────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Precificação IF"

app.index_string = '''<!DOCTYPE html>
<html>
  <head>
    {%metas%}
    <title>Precificação IF</title>
    {%favicon%}
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">
    {%css%}
  </head>
  <body>
    {%app_entry%}
    <footer>{%config%}{%scripts%}{%renderer%}</footer>
  </body>
</html>'''

# ── Helpers ───────────────────────────────────────────────────────────────────
def brl(v):
    neg = v < 0
    s = f"R$ {abs(v):,.2f}".replace(',','X').replace('.',',').replace('X','.')
    return f"−{s}" if neg else s

def pct(v, dec=4): return f"{v:.{dec}f}%"

PLOTLY_BASE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='JetBrains Mono', color='#4E5C7A', size=10),
    margin=dict(l=4, r=4, t=4, b=4),
    hoverlabel=dict(bgcolor='#111828', bordercolor='rgba(201,169,108,0.3)',
                    font=dict(family='JetBrains Mono', color='#DDE3EF', size=11)),
)

RECEITA_BASE = carregar(list(RECEITAS.keys())[0])

def ind_row(label, value, cls=''):
    return html.Div([
        html.Span(label, className='ind-name'),
        html.Span(value, className=f'ind-val {cls}'),
    ], className='ind-row')

def metric_card(label, value, sub='', cls='', val_cls='gold'):
    return html.Div([
        html.Div(label, className='metric-label'),
        html.Div(value, className=f'metric-value {val_cls}'),
        html.Span(sub, className=f'metric-badge {cls}') if sub else html.Div(),
    ], className='metric-card b-metric')

def section(title, children, style=None):
    return html.Div([
        html.Div(title, className='form-label'),
        *children,
    ], className='form-section', style=style or {})

def inp(id_, label, value, step=0.01, mn=0, mx=9999, fmt='%.4f', type_='number'):
    return html.Div([
        html.Div(label, className='form-label'),
        dcc.Input(id=id_, type=type_, value=value, step=step, min=mn, max=mx,
                  debounce=True,
                  style={'width':'100%','background':'#0C1020','border':'1px solid rgba(255,255,255,0.055)',
                         'borderRadius':'9px','color':'#DDE3EF','fontFamily':'JetBrains Mono',
                         'fontSize':'13px','padding':'7px 10px'}),
    ], className='form-group')

def alert(msg, tipo='ok'):
    return html.Div(msg, className=f'alert-box alert-{tipo}')

def chart_fla_vp(df_fluxo, tc=0):
    """Gráfico FLA VP por período."""
    df = df_fluxo[df_fluxo['t'] > 0].copy()
    colors = ['rgba(201,169,108,0.5)' if (tc > 0 and row['t'] <= tc) else '#C9A96C'
              for _, row in df.iterrows()]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['t'], y=df['FLA_VP'],
        marker_color=colors,
        hovertemplate='Período %{x}<br>FLA VP: R$ %{y:,.2f}<extra></extra>',
        name='FLA VP',
    ))
    fig.add_hline(y=0, line_color='rgba(248,113,113,0.5)', line_width=1)
    fig.update_layout(**PLOTLY_BASE,
        xaxis=dict(showgrid=False, zeroline=False, title='Período', titlefont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.03)', zeroline=False,
                   tickprefix='R$ ', tickformat=',.0f'),
        hovermode='x unified')
    return fig

def chart_sda_sdp(df_fluxo):
    """Evolução SDA e SDP."""
    df = df_fluxo.copy()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['t'], y=df['SDA'],
        line=dict(color='#C9A96C', width=1.8, shape='spline', smoothing=0.4),
        hovertemplate='t=%{x}<br>SDA: R$ %{y:,.2f}<extra>Ativo</extra>',
        fill='tozeroy', fillcolor='rgba(201,169,108,0.04)', name='Ativo'))
    fig.add_trace(go.Scatter(x=df['t'], y=df['SDP'],
        line=dict(color='#60A5FA', width=1.8, shape='spline', smoothing=0.4),
        hovertemplate='t=%{x}<br>SDP: R$ %{y:,.2f}<extra>Passivo</extra>',
        name='Passivo'))
    fig.update_layout(**PLOTLY_BASE,
        xaxis=dict(showgrid=False, zeroline=False, title='Período', titlefont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.03)',
                   zeroline=False, tickprefix='R$ ', tickformat=',.0f'),
        legend=dict(font=dict(size=10, color='#4E5C7A'), bgcolor='rgba(0,0,0,0)',
                    x=0, y=1.1, orientation='h'),
        hovermode='x unified')
    return fig

def chart_decomp(df_fluxo):
    """Decomposição do spread."""
    df = df_fluxo[df_fluxo['t'] > 0].copy()
    fig = go.Figure()
    comps = [('EBP', 'Funding', '#60A5FA'), ('IPP1', 'IPP', '#F87171'),
             ('EPE', 'Perda Esp.', '#F472B6'), ('ir_cs', 'IR/CS', '#A78BFA'),
             ('pasep_cof', 'PASEP+COF', '#C9A96C'), ('MG', 'Margem', '#34D399')]
    for col, name, color in comps:
        if col in df.columns:
            fig.add_trace(go.Bar(x=df['t'], y=df[col].abs(),
                marker_color=color, name=name,
                hovertemplate=f'{name}: R$ %{{y:,.2f}}<extra></extra>'))
    fig.update_layout(**PLOTLY_BASE,
        barmode='stack',
        xaxis=dict(showgrid=False, zeroline=False, title='Período', titlefont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.03)',
                   zeroline=False, tickprefix='R$ ', tickformat=',.0f'),
        legend=dict(font=dict(size=10, color='#4E5C7A'), bgcolor='rgba(0,0,0,0)',
                    orientation='h', x=0, y=1.12),
        hovermode='x unified')
    return fig

def chart_ratings(linhas, rar_min, rsple_min):
    """RAR_G e RSPLE por rating."""
    linhas_ok = [l for l in linhas if isinstance(l.get('RAR_G %'), float)]
    if not linhas_ok: return go.Figure()
    fig = go.Figure()
    rats = [l['Rating'] for l in linhas_ok]
    fig.add_trace(go.Scatter(x=rats, y=[l['RAR_G %'] for l in linhas_ok],
        line=dict(color='#C9A96C', width=2), mode='lines+markers',
        marker=dict(size=7, color=['#34D399' if l.get('Viável') else '#F87171' for l in linhas_ok]),
        name='RAR_G', hovertemplate='%{x}<br>RAR_G: %{y:.4f}%<extra></extra>'))
    fig.add_trace(go.Scatter(x=rats, y=[l.get('RSPLE %', 0) for l in linhas_ok],
        line=dict(color='#60A5FA', width=2, dash='dot'), mode='lines',
        name='RSPLE', hovertemplate='%{x}<br>RSPLE: %{y:.4f}%<extra></extra>'))
    fig.add_hline(y=rar_min, line_color='rgba(201,169,108,0.4)',
                  line_width=1, line_dash='dash', annotation_text=f'mín {rar_min}%')
    fig.update_layout(**PLOTLY_BASE,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.03)',
                   zeroline=False, ticksuffix='%'),
        legend=dict(font=dict(size=10, color='#4E5C7A'), bgcolor='rgba(0,0,0,0)',
                    x=0, y=1.12, orientation='h'),
        hovermode='x unified')
    return fig

# ── NAV ───────────────────────────────────────────────────────────────────────
NAV = [('📊','Parâmetros'),('📐','Fórmulas'),('🏦','Rating & PE'),('💰','Funding'),('📈','Resultados')]

# ── LAYOUT ────────────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Store(id='store-resultado', data=None),
    dcc.Store(id='store-sim', data=None),
    dcc.Store(id='store-nav', data='Parâmetros'),
    dcc.Store(id='store-tab', data='operacao'),

    html.Div([
        # SIDEBAR
        html.Div([
            html.Div('P', className='sidebar-logo'),
            *[html.Div([icon, html.Span(label, className='tooltip')],
                       className='nav-item', id=f'nav-{label.replace(" ","_").replace("&","e")}',
                       n_clicks=0)
              for icon, label in NAV],
            html.Div(className='sidebar-sep'),
            html.Div(['⚙', html.Span('Configurações', className='tooltip')],
                     className='nav-item nav-bottom'),
        ], className='sidebar'),

        # MAIN
        html.Div([
            # HEADER
            html.Div([
                html.Div([
                    html.Div('Precificação de Crédito', className='header-greet'),
                    html.Div(datetime.today().strftime('%d/%m/%Y — IF Crédito PPS'),
                             className='header-sub'),
                ]),
                html.Div([
                    html.Div(id='alert-area'),
                    html.Button('⚡ Calcular', id='btn-calcular', n_clicks=0,
                                className='btn btn-gold'),
                    html.Button('🔄 Simular Ratings', id='btn-simular', n_clicks=0,
                                className='btn'),
                ], className='header-right'),
            ], className='header'),

            # CONTENT
            html.Div(id='main-content'),

        ], className='main'),
    ], className='layout'),
])

# ── PAINEL: PARÂMETROS ────────────────────────────────────────────────────────
def painel_parametros():
    op  = RECEITA_BASE['params_op']
    cst = RECEITA_BASE['params_custo']
    rsc = RECEITA_BASE['params_risco']
    return html.Div([
        html.Div([
            # Col 1
            html.Div([
                section('Operação base', [
                    inp('inp-capital','Capital (R$)', 200000, 1000, 1000, 50000000),
                    inp('inp-prazo','Prazo (meses)', 60, 1, 1, 360),
                    inp('inp-carencia','Carência (meses)', 12, 1, 0, 360),
                    inp('inp-lamb','λ Margem % a.m.', 0.16, 0.01, 0, 5),
                ]),
            ], style={'flex':'1','minWidth':0}),

            # Col 2
            html.Div([
                section('Taxa ativa', [
                    inp('inp-taxa-fixa','Taxa fixa % a.m.', 1.43, 0.01, 0.01, 20),
                    inp('inp-cdi','CDI % a.m.', 1.08, 0.01, 0.01, 10),
                    html.Div([
                        html.Div('Referência', className='form-label'),
                        dcc.RadioItems(id='radio-modo-taxa',
                            options=[{'label':'Fixa % a.m.','value':'fixa'},
                                     {'label':'% do CDI','value':'cdi'}],
                            value='fixa', inline=True,
                            style={'color':'#4E5C7A','fontSize':'12px','gap':'12px','display':'flex'}),
                    ], className='form-group'),
                    inp('inp-pct-cdi','% do CDI', 132.0, 1, 10, 500),
                    html.Div(id='taxa-equiv-display',
                             style={'fontFamily':'JetBrains Mono','fontSize':'11px','color':'#C9A96C','marginTop':'-8px','marginBottom':'10px'}),
                ]),
                section('Carência — comportamento', [
                    html.Div([
                        html.Div('Juros na carência', className='form-label'),
                        dcc.RadioItems(id='radio-pagar-car',
                            options=[{'label':'Capitaliza','value':'cap'},
                                     {'label':'Paga corrente','value':'paga'}],
                            value='cap', inline=True,
                            style={'color':'#4E5C7A','fontSize':'12px','gap':'12px','display':'flex'}),
                    ], className='form-group'),
                    html.Div([
                        html.Div('Exigibilidade pós-carência', className='form-label'),
                        dcc.Dropdown(id='drop-exig',
                            options=[{'label':k,'value':str(v)} for k,v in
                                     {'Mensal':1,'Bimestral':2,'Trimestral':3,'Semestral':6,'Anual':12,'Bullet':'None','Proporcional':'-1'}.items()],
                            value='1', clearable=False,
                            style={'background':'#0C1020','border':'1px solid rgba(255,255,255,0.055)',
                                   'borderRadius':'9px','color':'#DDE3EF'}),
                    ], className='form-group'),
                ]),
            ], style={'flex':'1','minWidth':0}),

            # Col 3
            html.Div([
                section('Basileia III', [
                    inp('inp-fpr','FPR %', 75, 5, 0, 150),
                    inp('inp-k','K regulatório %', 11, 0.25, 5, 20),
                    inp('inp-kp','Kp prudencial %', 9.75, 0.25, 5, 20),
                    inp('inp-f','F alavancagem', 10.95, 0.05, 1, 30),
                    inp('inp-fcc','FCC %', 20, 5, 0, 100),
                ]),
            ], style={'flex':'1','minWidth':0}),

            # Col 4
            html.Div([
                section('Custos e tributos', [
                    inp('inp-custo-cont','Custo contrat. R$', 0, 100, 0, 100000),
                    inp('inp-alfa-pc','PASEP+COFINS %', 4.65, 0.01, 0, 10),
                    inp('inp-alfa-iss','ISS %', 5.0, 0.1, 0, 10),
                    inp('inp-alfa-ir','IRPJ+CSLL %', 45.0, 1, 0, 60),
                ]),
                section('Provisão IPP', [
                    inp('inp-fase1','IPP Fase1 % a.m.', 0.175, 0.005, 0, 1),
                    html.Div([
                        html.Div('Fase2 (flat t=0)', className='form-label'),
                        dcc.RadioItems(id='radio-fase2',
                            options=[{'label':'Não','value':'nao'},{'label':'Sim','value':'sim'}],
                            value='nao', inline=True,
                            style={'color':'#4E5C7A','fontSize':'12px','gap':'12px','display':'flex'}),
                    ], className='form-group'),
                    inp('inp-fase2-pct','Fase2 %', 1.5, 0.1, 0, 10),
                ]),
            ], style={'flex':'1','minWidth':0}),

        ], style={'display':'flex','gap':'24px'}),
    ])

# ── PAINEL: FÓRMULAS ──────────────────────────────────────────────────────────
SLOTS_OPTS = {
    'JA — Juros':      [('z036','z036 — Flat mensal ★'),('z15','z15 — Equiv. 1/n'),('z16','z16 — DU/252')],
    'PMTA':            [('price','Price ★'),('sac','SAC'),('bullet','Bullet')],
    'EBP — Encargo':   [('ebp_z3','ebp_z3 — DU/252 ★'),('ebp_z2','ebp_z2 — Equiv. 1/n'),('ebp_z4','ebp_z4 — DC/360')],
    'ECP — Capital':   [('z407','z407 — Matched ★'),('ecp_z68','ecp_z68 — Bullet')],
    'SP — Spread':     [('z175','z175 — Simples ★'),('z176','z176 — Com equaliz.')],
    'MG — Margem':     [('z182','z182 — Mensal ★'),('z180','z180 — DU/252'),('z393','z393 — Base Price')],
    'DPE — Provisão':  [('ipp','ipp — IPP 2 fases ★'),('z276','z276 — Mensal RBA')],
}
SLOTS_CHAVES = {'JA — Juros':'ativo.JA','PMTA':'ativo.PMTA','EBP — Encargo':'passivo.EBP',
                'ECP — Capital':'passivo.ECP','SP — Spread':'fluxo.SP','MG — Margem':'fluxo.MG','DPE — Provisão':'fluxo.DPE'}
SLOTS_DEFAULTS = {'ativo.JA':'z036','ativo.PMTA':'price','passivo.EBP':'ebp_z3','passivo.ECP':'z407','fluxo.SP':'z175','fluxo.MG':'z182','fluxo.DPE':'ipp'}
MODS = {'JA — Juros':'#1F3B6E','PMTA':'#1F3B6E','EBP — Encargo':'#1A5C3A','ECP — Capital':'#1A5C3A',
        'SP — Spread':'#4A1080','MG — Margem':'#4A1080','DPE — Provisão':'#4A1080'}

def painel_formulas():
    rows = []
    for slot_nome, opts in SLOTS_OPTS.items():
        cor = MODS.get(slot_nome, '#854F0B')
        chave = SLOTS_CHAVES.get(slot_nome, slot_nome)
        default = SLOTS_DEFAULTS.get(chave, opts[0][0])
        rows.append(html.Div([
            html.Div([
                html.Div(slot_nome, style={'fontSize':'11px','fontWeight':'600','color':cor,'fontFamily':'JetBrains Mono','width':'160px','flexShrink':'0'}),
                dcc.RadioItems(
                    id={'type':'slot-radio','index':chave},
                    options=[{'label':lbl,'value':val} for val,lbl in opts],
                    value=default, inline=True,
                    style={'color':'#4E5C7A','fontSize':'11px','gap':'16px','display':'flex','flexWrap':'wrap'},
                    inputStyle={'accentColor':cor},
                ),
            ], style={'display':'flex','alignItems':'center','gap':'16px','padding':'10px 0',
                      'borderBottom':'1px solid rgba(255,255,255,0.055)'}),
        ]))
    return html.Div([
        html.Div([
            html.Div('Seleção de fórmulas Z por slot', className='card-title'),
            html.Div('Clique para selecionar a fórmula de cada módulo', className='card-sub'),
        ], className='card-header'),
        *rows,
        html.Div([
            html.Div('Variantes avançadas disponíveis:', style={'fontSize':'10px','color':'#4E5C7A','marginTop':'16px','marginBottom':'8px','letterSpacing':'1px','textTransform':'uppercase'}),
            html.Div([
                html.Span('z17 DC/360', style={'background':'#FFF3E010','border':'1px solid rgba(201,169,108,.2)','borderRadius':'99px','padding':'3px 10px','fontSize':'10px','color':'#C9A96C','fontFamily':'JetBrains Mono','marginRight':'6px'}),
                html.Span('z181 DC/360 MG', style={'background':'#FFF3E010','border':'1px solid rgba(201,169,108,.2)','borderRadius':'99px','padding':'3px 10px','fontSize':'10px','color':'#C9A96C','fontFamily':'JetBrains Mono','marginRight':'6px'}),
                html.Span('z277 DU/252 RBA', style={'background':'#EEF2FA10','border':'1px solid rgba(96,165,250,.2)','borderRadius':'99px','padding':'3px 10px','fontSize':'10px','color':'#60A5FA','fontFamily':'JetBrains Mono','marginRight':'6px'}),
                html.Span('F1097 % CDI', style={'background':'#EEF2FA10','border':'1px solid rgba(96,165,250,.2)','borderRadius':'99px','padding':'3px 10px','fontSize':'10px','color':'#60A5FA','fontFamily':'JetBrains Mono'}),
            ]),
        ]),
    ], className='glass-card', style={'padding':'24px'})

# ── PAINEL: RATING & PE ───────────────────────────────────────────────────────
def painel_rating():
    return html.Div([
        html.Div([
            # Config
            html.Div([
                html.Div([
                    html.Div('Critérios de viabilidade', className='card-title'),
                    html.Div('Define o que é considerado viável para a linha', className='card-sub'),
                ], className='card-header'),
                inp('inp-rar-min','RAR_G mínimo %', 8.0, 0.5, 0, 30),
                inp('inp-rsple-min','RSPLE mínimo %', 6.0, 0.5, 0, 30),
                inp('inp-lgd','LGD %', 60.0, 1, 0, 100),
                html.Div(className='divider'),
                html.Div('Taxa por rating', className='form-label', style={'marginTop':'16px'}),
                dcc.RadioItems(id='radio-modo-rating',
                    options=[{'label':'Taxa base para todos','value':'base'},
                             {'label':'Spread diferencial por letra','value':'delta'},
                             {'label':'Tabela individual','value':'tabela'}],
                    value='base',
                    style={'color':'#4E5C7A','fontSize':'12px','gap':'8px','display':'flex','flexDirection':'column'}),
                html.Div(id='rating-taxa-config', style={'marginTop':'12px'}),
            ], className='glass-card', style={'flex':'1','padding':'24px'}),

            # Ratings a simular
            html.Div([
                html.Div([
                    html.Div('Ratings a simular', className='card-title'),
                    html.Div('Selecione quais classes serão calculadas', className='card-sub'),
                ], className='card-header'),
                dcc.Checklist(id='check-ratings',
                    options=[{'label':r,'value':r} for r in RATINGS_ORDEM],
                    value=['A01','A03','A05','B01','B03','B05','C01','C03','D01','E01'],
                    inline=True,
                    style={'color':'#4E5C7A','fontSize':'11px','fontFamily':'JetBrains Mono',
                           'gap':'8px','display':'flex','flexWrap':'wrap'},
                    inputStyle={'accentColor':'#C9A96C'},
                ),
                html.Div(className='divider', style={'margin':'16px 0'}),
                html.Div('Mix esperado da carteira (%)', className='form-label'),
                html.Div([
                    html.Div([
                        html.Div(letra, style={'fontSize':'10px','color':'#4E5C7A','textAlign':'center','marginBottom':'4px','fontFamily':'JetBrains Mono'}),
                        dcc.Input(id=f'mix-{letra}', type='number',
                                  value={'A':40,'B':30,'C':20,'D':10,'E':0,'F':0,'G':0}[letra],
                                  min=0, max=100, step=5, debounce=True,
                                  style={'width':'100%','background':'#0C1020','border':'1px solid rgba(255,255,255,0.055)',
                                         'borderRadius':'9px','color':'#DDE3EF','fontFamily':'JetBrains Mono',
                                         'fontSize':'12px','padding':'5px 6px','textAlign':'center'}),
                    ], style={'flex':'1'})
                    for letra in ['A','B','C','D','E','F','G']
                ], style={'display':'flex','gap':'6px'}),
                html.Div(id='mix-soma', style={'fontSize':'11px','color':'#C9A96C','fontFamily':'JetBrains Mono','marginTop':'8px'}),
            ], className='glass-card', style={'flex':'1.5','padding':'24px'}),

        ], style={'display':'flex','gap':'14px'}),
    ])

# ── PAINEL: FUNDING ───────────────────────────────────────────────────────────
def painel_funding():
    rows = []
    for f in FAIXAS_PADRAO:
        tot = taxa_total_faixa(f['taxa_if_aa'], f['taxa_fs_aa'])
        rows.append(html.Div([
            html.Div(f['nome'][:40], className='faixa-nome'),
            html.Div(f"IF {f['taxa_if_aa']}%", style={'fontSize':'11px','color':'#4E5C7A','fontFamily':'JetBrains Mono','width':'70px','textAlign':'right'}),
            html.Div(f"+FS {f['taxa_fs_aa']}%", style={'fontSize':'11px','color':'#4E5C7A','fontFamily':'JetBrains Mono','width':'80px','textAlign':'right'}),
            html.Div(f"= {tot:.2f}% a.a.", className='faixa-val'),
            html.Div(f"({taxa_am_de_aa(tot):.4f}% a.m.)", style={'fontSize':'10px','color':'#29334A','fontFamily':'JetBrains Mono','width':'120px','textAlign':'right'}),
        ], className='faixa-row'))

    w = wacc_faixas(FAIXAS_PADRAO)
    return html.Div([
        html.Div([
            # Tabela de faixas
            html.Div([
                html.Div([
                    html.Div('Funding por faixas de cliente', className='card-title'),
                    html.Div('Taxa total ao mutuário = Taxa IF + Taxa FS', className='card-sub'),
                ], className='card-header'),
                html.Div([
                    html.Div([
                        html.Div('Faixa', style={'flex':'1','fontSize':'10px','color':'#4E5C7A','letterSpacing':'1px','textTransform':'uppercase'}),
                        html.Div('IF % a.a.', style={'width':'70px','textAlign':'right','fontSize':'10px','color':'#4E5C7A','letterSpacing':'1px','textTransform':'uppercase'}),
                        html.Div('FS % a.a.', style={'width':'80px','textAlign':'right','fontSize':'10px','color':'#4E5C7A','letterSpacing':'1px','textTransform':'uppercase'}),
                        html.Div('Total', style={'width':'100px','textAlign':'right','fontSize':'10px','color':'#4E5C7A','letterSpacing':'1px','textTransform':'uppercase'}),
                        html.Div('% a.m.', style={'width':'120px','textAlign':'right','fontSize':'10px','color':'#4E5C7A','letterSpacing':'1px','textTransform':'uppercase'}),
                    ], style={'display':'flex','padding':'0 0 8px 0','borderBottom':'1px solid rgba(255,255,255,0.055)'}),
                    *rows,
                ]),
            ], className='glass-card', style={'flex':'2','padding':'24px'}),

            # WACC e config
            html.Div([
                html.Div([
                    html.Div('Custo efetivo do passivo', className='card-title'),
                    html.Div('WACC ponderado das faixas', className='card-sub'),
                ], className='card-header'),
                html.Div(f"{w['wacc_aa']:.4f}%", className='metric-value gold'),
                html.Div('% a.a. (WACC)', style={'fontSize':'11px','color':'#4E5C7A','marginBottom':'12px'}),
                html.Div(f"{w['wacc_am']:.6f}%", className='metric-value', style={'fontSize':'20px'}),
                html.Div('% a.m.', style={'fontSize':'11px','color':'#4E5C7A','marginBottom':'20px'}),
                html.Div(className='divider'),
                html.Div([
                    html.Div('Usar WACC das faixas', className='form-label', style={'marginTop':'16px'}),
                    dcc.RadioItems(id='radio-usar-wacc',
                        options=[{'label':'Sim','value':'sim'},{'label':'Não (CDI manual)','value':'nao'}],
                        value='sim', inline=True,
                        style={'color':'#4E5C7A','fontSize':'12px','gap':'12px','display':'flex'},
                        inputStyle={'accentColor':'#C9A96C'}),
                ]),
                html.Div(id='wacc-display', style={'marginTop':'12px','fontSize':'11px','color':'#C9A96C','fontFamily':'JetBrains Mono'}),
                html.Div(className='divider', style={'margin':'16px 0'}),
                html.Div('Configuração futura: adicione e edite faixas diretamente nesta tela.', style={'fontSize':'11px','color':'#29334A','fontFamily':'JetBrains Mono','lineHeight':'1.6'}),
            ], className='glass-card', style={'flex':'1','padding':'24px'}),

        ], style={'display':'flex','gap':'14px'}),
    ])

# ── PAINEL: RESULTADOS ────────────────────────────────────────────────────────
def painel_resultados(resultado=None, sim=None):
    if not resultado and not sim:
        return html.Div([
            html.Div('Nenhum cálculo realizado', style={'textAlign':'center','padding':'80px','color':'#4E5C7A','fontSize':'15px'}),
            html.Div('Configure os parâmetros e clique em ⚡ Calcular ou 🔄 Simular Ratings',
                     style={'textAlign':'center','color':'#29334A','fontSize':'12px','fontFamily':'JetBrains Mono'}),
        ])

    items = []

    # ── MÉTRICAS principais ──────────────────────────────────────────────────
    if resultado:
        rs = resultado['resumo']
        rsple = rs.get('RSPLE %', 0) or 0
        rar_g = rs.get('RAR_G % (gestão, F1183)', 0) or 0
        tir   = rs.get('TIR % a.a.')
        fla   = rs.get('FLA VP (Σ) → 0', 0) or 0
        sda_ok= abs(rs.get('SDA final',99)) < 50

        items += [
            metric_card('RSPLE', pct(rsple), '★ retorno sobre PL', 'badge-up' if rsple>=6 else 'badge-down', 'gold'),
            metric_card('RAR_G', pct(rar_g), 'gestão — F1183', 'badge-up' if rar_g>=8 else 'badge-down', 'green' if rar_g>=8 else 'red'),
            metric_card('TIR', f"{tir:.4f}% a.a." if tir else '—', 'taxa interna retorno', '', ''),
            metric_card('FLA VP', f"{fla:,.0f}", '✓ fechado' if sda_ok else '⚠ verificar',
                        'badge-up' if abs(fla)<200 else 'badge-down', 'green' if abs(fla)<200 else 'red'),
        ]

        df = resultado['fluxo']
        # Gráfico SDA/SDP
        items.append(html.Div([
            html.Div([
                html.Div([
                    html.Div('Evolução SDA / SDP', className='card-title'),
                    html.Div('Saldo ativo vs passivo por período', className='card-sub'),
                ]),
            ], className='card-header'),
            dcc.Graph(figure=chart_sda_sdp(df), config={'displayModeBar':False}, style={'height':'220px'}),
        ], className='glass-card b-chart'))

        # Indicadores detalhe
        items.append(html.Div([
            html.Div([html.Div('Fluxo acumulado', className='card-title')], className='card-header'),
            ind_row('Total PMTA',   brl(rs.get('Total PMTA',0))),
            ind_row('Total JA',     brl(rs.get('Total JA',0))),
            ind_row('Custo CDI',    brl(rs.get('Total EBP (CDI)',0))),
            ind_row('Spread Bruto', brl(rs.get('Total SP',0)), 'gold'),
            ind_row('Total MG',     brl(rs.get('Total MG',0)), 'green'),
            ind_row('IPP Fase1',    brl(rs.get('Total IPP Fase1',0))),
            ind_row('Perda Esp.',   brl(rs.get('Total EPE',0))),
            ind_row('IR+CSLL',      brl(rs.get('Total IR/CS',0))),
        ], className='glass-card b-accounts', style={'padding':'22px'}))

        # FLA VP chart
        items.append(html.Div([
            html.Div([
                html.Div([
                    html.Div('FLA VP por período', className='card-title'),
                    html.Div('Barras douradas = carência', className='card-sub'),
                ]),
            ], className='card-header'),
            dcc.Graph(figure=chart_fla_vp(df, rs.get('Prazo (T)',0)),
                      config={'displayModeBar':False}, style={'height':'200px'}),
        ], className='glass-card b-tx'))

        # Decomposição spread
        items.append(html.Div([
            html.Div([
                html.Div([
                    html.Div('Decomposição do spread', className='card-title'),
                    html.Div('Funding | IPP | Perda | IR/CS | PASEP | Margem', className='card-sub'),
                ]),
            ], className='card-header'),
            dcc.Graph(figure=chart_decomp(df),
                      config={'displayModeBar':False}, style={'height':'200px'}),
        ], className='glass-card b-donut'))

    # ── SIMULAÇÃO POR RATING ─────────────────────────────────────────────────
    if sim:
        linhas = sim.get('linhas', [])
        front  = sim.get('fronteira')
        n_v    = sim.get('n_viaveis', 0)
        n_t    = sim.get('n_total', 0)

        # Banner fronteira
        items.append(html.Div([
            html.Div([
                html.Div('Fronteira de viabilidade', style={'fontSize':'10px','fontWeight':'700',
                    'color':'#C9A96C','textTransform':'uppercase','letterSpacing':'1px','marginBottom':'6px'}),
                html.Div(front or 'Nenhum', style={'fontSize':'32px','fontWeight':'700',
                    'color':'#C9A96C','fontFamily':'Instrument Serif','fontStyle':'italic','marginBottom':'6px'}),
                html.Div(f"{n_v}/{n_t} ratings atingem os critérios mínimos",
                         style={'fontSize':'12px','color':'#4E5C7A','fontFamily':'JetBrains Mono'}),
            ], style={'flex':'1'}),
            html.Div([
                dcc.Graph(figure=chart_ratings(linhas, 8.0, 6.0),
                          config={'displayModeBar':False}, style={'height':'120px','width':'100%'}),
            ], style={'flex':'2'}),
        ], className='glass-card b-flow', style={'display':'flex','alignItems':'center','gap':'32px','padding':'24px'}))

        # Tabela de ratings
        rows_rat = []
        for l in linhas:
            if 'Erro' in l: continue
            viavel = l.get('Viável')
            front_r= (l['Rating'] == front)
            cls    = 'fronteira' if front_r else ('viavel' if viavel else 'nviavel')
            rows_rat.append(html.Tr([
                html.Td(l['Rating'], style={'fontWeight':'700' if front_r else '400'}),
                html.Td(f"{l.get('PD % a.a.',0):.2f}%"),
                html.Td(f"{l.get('PE % a.m.',0):.4f}%"),
                html.Td(f"{l.get('RSPLE %',0):.4f}%"),
                html.Td(f"{l.get('RAR_G %',0):.4f}%"),
                html.Td(brl(l.get('Total SP',0))),
                html.Td(brl(l.get('Total MG',0))),
                html.Td(f"{l.get('FLA VP',0):,.0f}"),
                html.Td('✓' if viavel else '✗',
                        style={'color':'#34D399' if viavel else '#F87171','fontWeight':'700'}),
            ], className=cls))

        items.append(html.Div([
            html.Div([html.Div('Simulação por rating', className='card-title')], className='card-header'),
            html.Table([
                html.Thead(html.Tr([
                    html.Th(h) for h in ['Rating','PD%aa','PE%am','RSPLE%','RAR_G%','Total SP','Total MG','FLA VP','Ok']
                ])),
                html.Tbody(rows_rat),
            ], className='prec-table'),
        ], className='glass-card b-flow', style={'padding':'22px','overflowX':'auto'}))

    if not items:
        return html.Div('Nenhum resultado disponível', style={'textAlign':'center','padding':'40px','color':'#4E5C7A'})

    return html.Div(items, className='bento')

# ── CALLBACKS ─────────────────────────────────────────────────────────────────

# Navegação
@app.callback(
    Output('main-content','children'),
    Output('store-nav','data'),
    [Input(f'nav-{l.replace(" ","_").replace("&","e")}','n_clicks') for _,l in NAV] +
    [Input('store-resultado','data'), Input('store-sim','data')],
    State('store-nav','data'),
    prevent_initial_call=False,
)
def navigate(*args):
    n_nav = len(NAV)
    clicks = args[:n_nav]
    resultado, sim, current = args[n_nav], args[n_nav+1], args[n_nav+2]

    ctx = callback_context
    if ctx.triggered:
        trig = ctx.triggered[0]['prop_id']
        for i, (_, label) in enumerate(NAV):
            nav_id = f'nav-{label.replace(" ","_").replace("&","e")}'
            if nav_id in trig:
                current = label
                break
        if 'store-resultado' in trig or 'store-sim' in trig:
            current = 'Resultados'

    panels = {
        'Parâmetros': painel_parametros,
        'Fórmulas':   painel_formulas,
        'Rating & PE':painel_rating,
        'Funding':    painel_funding,
        'Resultados': lambda: painel_resultados(resultado, sim),
    }
    return panels.get(current, painel_parametros)(), current

# Equivalência taxa CDI
@app.callback(
    Output('taxa-equiv-display','children'),
    Input('inp-taxa-fixa','value'),
    Input('inp-pct-cdi','value'),
    Input('inp-cdi','value'),
    Input('radio-modo-taxa','value'),
)
def atualiza_equiv(taxa_fixa, pct_cdi_v, cdi, modo):
    cdi = cdi or 1.08
    if modo == 'fixa':
        taxa = taxa_fixa or 1.43
        return f"≈ {pct_cdi_de_taxa(taxa, cdi):.1f}% do CDI"
    else:
        pct = pct_cdi_v or 100.0
        tx  = taxa_de_pct_cdi(pct, cdi)
        return f"= {tx:.4f}% a.m."

# Config taxa por rating
@app.callback(
    Output('rating-taxa-config','children'),
    Input('radio-modo-rating','value'),
    Input('inp-taxa-fixa','value'),
    Input('inp-cdi','value'),
)
def config_rating_taxa(modo, taxa_base, cdi):
    taxa_base = taxa_base or 1.43; cdi = cdi or 1.08
    if modo == 'base':
        return html.Div(f"Taxa {taxa_base:.4f}% a.m. para todos os ratings",
                        style={'fontSize':'11px','color':'#C9A96C','fontFamily':'JetBrains Mono'})
    elif modo == 'delta':
        return html.Div([
            html.Div('Delta por letra (pp a.m.):', style={'fontSize':'10px','color':'#4E5C7A','marginBottom':'8px'}),
            html.Div([
                html.Div([
                    html.Div(l, style={'fontSize':'10px','textAlign':'center','color':'#4E5C7A','fontFamily':'JetBrains Mono','marginBottom':'3px'}),
                    dcc.Input(id=f'delta-{l}', type='number',
                              value={'A':0.0,'B':0.2,'C':0.4,'D':0.7,'E':1.0,'F':1.5,'G':2.0}[l],
                              step=0.05, debounce=True,
                              style={'width':'100%','background':'#0C1020','border':'1px solid rgba(255,255,255,0.055)',
                                     'borderRadius':'7px','color':'#DDE3EF','fontFamily':'JetBrains Mono',
                                     'fontSize':'11px','padding':'4px 5px','textAlign':'center'}),
                ], style={'flex':'1'})
                for l in ['A','B','C','D','E','F','G']
            ], style={'display':'flex','gap':'4px'}),
        ])
    else:
        return html.Div('Tabela individual disponível na próxima versão.',
                        style={'fontSize':'11px','color':'#4E5C7A','fontFamily':'JetBrains Mono'})

# Mix soma
@app.callback(
    Output('mix-soma','children'),
    [Input(f'mix-{l}','value') for l in ['A','B','C','D','E','F','G']],
)
def soma_mix(*vals):
    s = sum((v or 0) for v in vals)
    ok = abs(s-100) < 1
    return f"Soma: {s:.0f}% {'✓' if ok else '⚠ deve ser 100%'}"

# WACC display
@app.callback(
    Output('wacc-display','children'),
    Input('radio-usar-wacc','value'),
    Input('inp-cdi','value'),
)
def wacc_display(usar, cdi):
    cdi = cdi or 1.08
    w = wacc_faixas(FAIXAS_PADRAO)
    if usar == 'sim':
        return f"Custo passivo: {w['wacc_am']:.6f}% a.m. (WACC faixas)"
    return f"Custo passivo: {cdi:.4f}% a.m. (CDI manual)"

# ── CALCULAR ──────────────────────────────────────────────────────────────────
@app.callback(
    Output('store-resultado','data'),
    Output('alert-area','children'),
    Input('btn-calcular','n_clicks'),
    State('inp-capital','value'), State('inp-prazo','value'),
    State('inp-carencia','value'), State('inp-lamb','value'),
    State('inp-taxa-fixa','value'), State('inp-pct-cdi','value'),
    State('inp-cdi','value'), State('radio-modo-taxa','value'),
    State('inp-fpr','value'), State('inp-k','value'),
    State('inp-kp','value'), State('inp-f','value'), State('inp-fcc','value'),
    State('inp-fase1','value'), State('radio-fase2','value'),
    State('inp-fase2-pct','value'),
    State('inp-alfa-pc','value'), State('inp-alfa-iss','value'),
    State('inp-alfa-ir','value'), State('inp-custo-cont','value'),
    State({'type':'slot-radio','index':ALL},'value'),
    State({'type':'slot-radio','index':ALL},'id'),
    State('radio-usar-wacc','value'),
    State('radio-pagar-car','value'),
    State('drop-exig','value'),
    prevent_initial_call=True,
)
def calcular(n_clicks, C, T, tc, lamb, taxa_fixa, pct_cdi_v, cdi, modo_taxa,
             FPR, K, Kp, F_aval, FCC, fase1, usar_fase2, fase2_pct,
             alfa_pc, alfa_iss, alfa_ir, custo_cont,
             slot_vals, slot_ids, usar_wacc, pagar_car, exig_str):
    if not n_clicks: return dash.no_update, html.Div()

    try:
        C=float(C or 200000); T=int(T or 60); tc=int(tc or 0); lamb=float(lamb or 0.16)
        cdi=float(cdi or 1.08)
        i_am=float(taxa_fixa or 1.43) if modo_taxa=='fixa' else taxa_de_pct_cdi(float(pct_cdi_v or 100), cdi)

        # Alertas
        alerts=[]
        if i_am < cdi: alerts.append(alert('⚠ Taxa ativa abaixo do CDI — spread negativo','warning'))
        if tc > T*0.5: alerts.append(alert(f'⚠ Carência ({tc}m) > 50% do prazo ({T}m)','warning'))

        w = wacc_faixas(FAIXAS_PADRAO)
        wacc = w['wacc_am'] if usar_wacc=='sim' else cdi

        exig_map={'1':1,'2':2,'3':3,'6':6,'12':12,'None':None,'-1':-1}
        z_J = exig_map.get(str(exig_str), 1)

        rc = copy.deepcopy(RECEITA_BASE)
        rc['params_op'].update(dict(
            C=C, T=T, tc=tc, i_am=i_am, cdi_am=wacc, PMTA_fixo=None,
            pagar_juros_carencia=(pagar_car=='paga'), z_J_ativo=z_J,
            CVSC_aa=13.0, DU=21,
        ))
        rc['params_margem']['lamb_am'] = lamb
        rc['params_risco'].update(dict(
            FPR=float(FPR or 75), K=float(K or 11), Kp=float(Kp or 9.75),
            F=float(F_aval or 10.95), FCC=float(FCC or 20),
            fase1_am=float(fase1 or 0.175),
            usa_fase2=(usar_fase2=='sim'), fase2_pct=float(fase2_pct or 1.5),
        ))
        rc['params_custo'].update(dict(
            custo_cont=float(custo_cont or 0), alfa_pc=float(alfa_pc or 4.65),
            alfa_iss=float(alfa_iss or 5), alfa_ir_cs=float(alfa_ir or 45),
        ))

        # Slots
        for sid, sval in zip(slot_ids, slot_vals):
            chave = sid['index']
            if 'perf' not in chave and 'enc' not in chave:
                rc['slots'][chave] = sval

        res = executar(rc)
        res_serial = {
            'resumo': {k: (float(v) if isinstance(v,(int,float)) else str(v) if v is not None else None)
                       for k,v in res['resumo'].items()},
            'fluxo': res['fluxo'].to_dict('records'),
        }
        return res_serial, html.Div(alerts)

    except Exception as e:
        return dash.no_update, alert(f'Erro: {str(e)[:100]}','error')

# ── SIMULAR ───────────────────────────────────────────────────────────────────
@app.callback(
    Output('store-sim','data'),
    Input('btn-simular','n_clicks'),
    State('inp-capital','value'), State('inp-prazo','value'),
    State('inp-carencia','value'), State('inp-lamb','value'),
    State('inp-taxa-fixa','value'), State('inp-cdi','value'),
    State('radio-modo-taxa','value'),
    State('inp-fpr','value'), State('inp-k','value'),
    State('inp-kp','value'), State('inp-f','value'), State('inp-fcc','value'),
    State('inp-fase1','value'),
    State('inp-alfa-pc','value'), State('inp-alfa-iss','value'),
    State('inp-alfa-ir','value'),
    State('check-ratings','value'),
    State('inp-rar-min','value'), State('inp-rsple-min','value'),
    State('inp-lgd','value'),
    State('radio-modo-rating','value'),
    State({'type':'slot-radio','index':ALL},'value'),
    State({'type':'slot-radio','index':ALL},'id'),
    State('radio-usar-wacc','value'),
    State('radio-pagar-car','value'),
    State('drop-exig','value'),
    prevent_initial_call=True,
)
def simular(n_clicks, C, T, tc, lamb, taxa_fixa, cdi, modo_taxa,
            FPR, K, Kp, F_aval, FCC, fase1,
            alfa_pc, alfa_iss, alfa_ir,
            ratings_sel, rar_min, rsple_min, lgd_v,
            modo_rating, slot_vals, slot_ids,
            usar_wacc, pagar_car, exig_str):
    if not n_clicks or not ratings_sel: return dash.no_update

    try:
        C=float(C or 200000); T=int(T or 60); tc=int(tc or 0); lamb=float(lamb or 0.16)
        cdi=float(cdi or 1.08)
        i_am=float(taxa_fixa or 1.43) if modo_taxa=='fixa' else taxa_de_pct_cdi(float(taxa_fixa or 100), cdi)
        w = wacc_faixas(FAIXAS_PADRAO)
        wacc = w['wacc_am'] if usar_wacc=='sim' else cdi
        rar_min=float(rar_min or 8); rsple_min=float(rsple_min or 6); lgd_v=float(lgd_v or 60)
        exig_map={'1':1,'2':2,'3':3,'6':6,'12':12,'None':None,'-1':-1}
        z_J=exig_map.get(str(exig_str),1)

        rc = copy.deepcopy(RECEITA_BASE)
        rc['params_op'].update(dict(C=C,T=T,tc=tc,i_am=i_am,cdi_am=wacc,PMTA_fixo=None,
            pagar_juros_carencia=(pagar_car=='paga'),z_J_ativo=z_J,CVSC_aa=13.0,DU=21))
        rc['params_margem']['lamb_am']=lamb
        rc['params_risco'].update(dict(FPR=float(FPR or 75),K=float(K or 11),Kp=float(Kp or 9.75),
            F=float(F_aval or 10.95),FCC=float(FCC or 20),fase1_am=float(fase1 or 0.175)))
        rc['params_custo'].update(dict(alfa_pc=float(alfa_pc or 4.65),
            alfa_iss=float(alfa_iss or 5),alfa_ir_cs=float(alfa_ir or 45)))
        for sid,sval in zip(slot_ids,slot_vals):
            chave=sid['index']
            if 'perf' not in chave and 'enc' not in chave:
                rc['slots'][chave]=sval

        tab_rat=build_tabela(None, lgd_v)
        crit=CriteriosViabilidade(rar_g_min=rar_min, rsple_min=rsple_min)

        delta_sim=None
        if modo_rating=='delta':
            delta_sim={cod:{'A':0,'B':0.2,'C':0.4,'D':0.7,'E':1.0,'F':1.5,'G':2.0}.get(cod[0],0) for cod in RATINGS_ORDEM}

        if delta_sim:
            sim=simular_portfolio_v2(rc,tab_rat,crit,ratings_sel,None,delta_sim)
        else:
            sim=simular_portfolio(rc,tab_rat,crit,ratings_sel)

        # Serializa
        linhas_s=[]
        for l in sim['linhas']:
            ls={k:(float(v) if isinstance(v,(int,float)) else (True if v is True else (False if v is False else str(v) if v is not None else None)))
               for k,v in l.items() if k!='_resumo'}
            linhas_s.append(ls)

        return {'linhas':linhas_s,'fronteira':sim['fronteira'],
                'n_viaveis':sim['n_viaveis'],'n_total':sim['n_total']}

    except Exception as e:
        return dash.no_update

# ── DESERIALIZA RESULTADO PARA OS GRÁFICOS ────────────────────────────────────
@app.callback(
    Output('main-content','children'),
    Input('store-resultado','data'),
    Input('store-sim','data'),
    State('store-nav','data'),
    prevent_initial_call=True,
)
def atualiza_resultado(resultado_raw, sim_raw, nav):
    resultado = None
    if resultado_raw:
        df = pd.DataFrame(resultado_raw['fluxo'])
        resultado = {'resumo': resultado_raw['resumo'], 'fluxo': df}
    return painel_resultados(resultado, sim_raw)

# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\n" + "═"*52)
    print("  📊  Precificação IF — Noir Gold Edition")
    print("═"*52)
    print("  ▸  http://localhost:8050")
    print("  ▸  Ctrl+C para parar")
    print("═"*52 + "\n")
    app.run(debug=False, port=8050)
