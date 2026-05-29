"""
Indicadores fundamentalistas por ativo.

Provedor:
  - "investidor10" → investidor10.com.br (scraping HTML, ações e FIIs)

Para adicionar um novo provedor:
  1. Implemente _from_<nome>(ticker) → dict com as chaves de INDICATORS
  2. Registre em PROVIDERS
"""

# ---------------------------------------------------------------------------
# Metadados dos indicadores
# ---------------------------------------------------------------------------
INDICATORS = {
    "p_l":       {"label": "P/L",            "description": "Preço / Lucro. Quantos anos para recuperar o investimento pelo lucro atual. Quanto menor, mais barato.",          "fmt": "x"},
    "p_vp":      {"label": "P/VP",           "description": "Preço / Valor Patrimonial. Abaixo de 1,0 negocia abaixo do patrimônio — muito relevante para FIIs.",              "fmt": "x"},
    "dy":        {"label": "Dividend Yield", "description": "Dividendos pagos nos últimos 12 meses em relação ao preço atual. Quanto maior, mais renda o ativo distribui.",    "fmt": "%"},
    "roe":       {"label": "ROE",            "description": "Retorno sobre Patrimônio Líquido. Acima de 15% é considerado bom.",                                               "fmt": "%"},
    "lpa":       {"label": "LPA",            "description": "Lucro Por Ação: lucro líquido ÷ total de ações.",                                                                 "fmt": "R$"},
    "vpa":       {"label": "VPA",            "description": "Valor Patrimonial por Ação: patrimônio líquido ÷ total de ações.",                                                "fmt": "R$"},
    "ev_ebitda": {"label": "EV/EBITDA",      "description": "Valor da empresa (incluindo dívida) dividido pelo EBITDA. Abaixo de 10 é considerado atrativo.",                  "fmt": "x"},
    "mrg_liq":   {"label": "Margem Líquida", "description": "Percentual do faturamento convertido em lucro líquido. Quanto maior, mais eficiente a operação.",                 "fmt": "%"},
    "div_patrim":{"label": "Dív/Patrim.",    "description": "Dívida bruta em relação ao patrimônio líquido. Quanto menor, menos alavancada.",                                  "fmt": "x"},
}

_EMPTY = {k: None for k in INDICATORS}


def _is_fii(ticker: str) -> bool:
    return ticker.upper().replace(".SA", "").endswith("11")


# ---------------------------------------------------------------------------
# Formatação de valores para exibição
# ---------------------------------------------------------------------------
def _fmt_value(value, fmt: str) -> str | None:
    if value is None:
        return None
    if fmt == "x":
        return f"{value:.2f}x"
    if fmt == "%":
        return f"{value:.2f}%"
    if fmt == "R$":
        formatted = f"{abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"
    return str(value)


# ---------------------------------------------------------------------------
# Provedor: Investidor10  (ações e FIIs)
# ---------------------------------------------------------------------------
def _from_investidor10(ticker: str) -> dict:
    import math
    import re
    import requests

    sym = ticker.upper().replace(".SA", "")
    is_fii = _is_fii(sym)
    path = "fiis" if is_fii else "acoes"
    url = f"https://investidor10.com.br/{path}/{sym.lower()}/"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        raise RuntimeError(f"Investidor10 indisponível para '{sym}': {e}")

    raw: dict[str, str] = {}

    # Padrão 1: _card (P/L, P/VP, DY exibidos em destaque)
    card_re = re.compile(
        r'<div class="_card[^"]*">\s*<div class="_card-header">\s*<div>\s*'
        r'<span[^>]*title="([^"]+)"[^>]*>.*?</span>.*?</div>\s*</div>\s*'
        r'<div class="_card-body">\s*(?:<[^>]*>\s*)*<span[^>]*>([^<]+)</span>',
        re.DOTALL,
    )
    for title, val in card_re.findall(html):
        raw[title.strip()] = val.strip()

    # Padrão 2: células de indicadores individuais
    def split_cells(h):
        out = []
        i = 0
        while True:
            s = h.find('<div class="cell"', i)
            if s == -1:
                break
            depth, j = 0, s
            while j < len(h):
                if h[j:j+4] == '<div':
                    depth += 1; j += 4
                elif h[j:j+6] == '</div>':
                    depth -= 1; j += 6
                    if depth == 0:
                        out.append(h[s:j]); break
                else:
                    j += 1
            i = j
        return out

    label_re = re.compile(r'>([A-ZÁÉÍÓÚÂÊÔ/][^<\n]{1,40}?)\s*<i\s+class="far fa-question-circle')
    value_re = re.compile(r'<div class="value[^"]*"[^>]*>\s*<span[^>]*>\s*([\d\.,\-]+%?)\s*</span>')

    for cell in split_cells(html):
        lm = label_re.search(cell)
        vm = value_re.search(cell)
        if lm and vm:
            key = lm.group(1).strip()
            if key not in raw:
                raw[key] = vm.group(1).strip()

    def to_float(*keys):
        for key in keys:
            val = raw.get(key, "")
            if not val or val in ("-", "—", "N/A"):
                continue
            cleaned = val.replace("R$", "").replace("%", "").replace(".", "").replace(",", ".").strip()
            try:
                f = float(cleaned)
                return None if (math.isnan(f) or math.isinf(f)) else round(f, 4)
            except ValueError:
                continue
        return None

    if is_fii:
        return {
            "p_l":       None,
            "p_vp":      to_float("P/VP"),
            "dy":        to_float("Dividend Yield", "DY"),
            "roe":       None,
            "lpa":       None,
            "vpa":       to_float("VP/COTA", "VPA"),
            "ev_ebitda": None,
            "mrg_liq":   None,
            "div_patrim":None,
        }
    return {
        "p_l":       to_float("P/L"),
        "p_vp":      to_float("P/VP"),
        "dy":        to_float("DY"),
        "roe":       to_float("ROE"),
        "lpa":       to_float("LPA"),
        "vpa":       to_float("VPA"),
        "ev_ebitda": to_float("EV/Ebitda", "EV/EBITDA"),
        "mrg_liq":   to_float("Margem Líquida", "MARG. LÍQUIDA"),
        "div_patrim":to_float("Dívida Bruta / Patrimônio"),
    }


# ---------------------------------------------------------------------------
# Registro de provedores
# ---------------------------------------------------------------------------
PROVIDERS = {
    "investidor10": {"fn": _from_investidor10, "label": "Investidor10", "supports_fii": True},
}


# ---------------------------------------------------------------------------
# Recomendação fundamentalista
# ---------------------------------------------------------------------------
def get_recommendation(indicators: list[dict]) -> dict:
    """
    Analisa os indicadores e retorna sinal de compra/venda/aguardar com justificativas.
    Retorna: {signal, score, reasons: [{text, type}]}
    """
    vals = {i["key"]: i["value"] for i in indicators}
    score = 0
    reasons = []

    def add(points, text, typ):
        nonlocal score
        score += points
        reasons.append({"text": text, "type": typ})

    p_l       = vals.get("p_l")
    p_vp      = vals.get("p_vp")
    dy        = vals.get("dy")
    roe       = vals.get("roe")
    ev_ebitda = vals.get("ev_ebitda")
    mrg_liq   = vals.get("mrg_liq")

    # P/L
    if p_l is not None:
        if p_l <= 0:
            add(-1, f"P/L negativo ({p_l:.2f}x) — empresa operando com prejuízo", "negative")
        elif p_l < 10:
            add(+2, f"P/L muito baixo ({p_l:.2f}x) — ação barata em relação ao lucro", "positive")
        elif p_l < 20:
            add(+1, f"P/L razoável ({p_l:.2f}x)", "neutral")
        elif p_l < 30:
            add( 0, f"P/L elevado ({p_l:.2f}x) — ação cara em relação ao lucro", "neutral")
        else:
            add(-2, f"P/L muito alto ({p_l:.2f}x) — valuação excessiva", "negative")

    # P/VP
    if p_vp is not None:
        if p_vp < 1.0:
            add(+2, f"P/VP abaixo de 1 ({p_vp:.2f}x) — negociando abaixo do patrimônio", "positive")
        elif p_vp < 1.5:
            add(+1, f"P/VP próximo ao patrimônio ({p_vp:.2f}x)", "neutral")
        elif p_vp < 3.0:
            add( 0, f"P/VP moderado ({p_vp:.2f}x)", "neutral")
        else:
            add(-1, f"P/VP elevado ({p_vp:.2f}x) — caro em relação ao patrimônio", "negative")

    # DY
    if dy is not None:
        if dy > 8:
            add(+2, f"Dividend Yield alto ({dy:.2f}%) — excelente geração de renda", "positive")
        elif dy > 5:
            add(+1, f"Dividend Yield bom ({dy:.2f}%)", "positive")
        elif dy > 2:
            add( 0, f"Dividend Yield moderado ({dy:.2f}%)", "neutral")
        else:
            add(-1, f"Dividend Yield baixo ({dy:.2f}%) — pouca distribuição", "negative")

    # ROE
    if roe is not None:
        if roe > 20:
            add(+2, f"ROE excelente ({roe:.2f}%) — alta rentabilidade sobre o patrimônio", "positive")
        elif roe > 15:
            add(+1, f"ROE bom ({roe:.2f}%)", "positive")
        elif roe > 10:
            add( 0, f"ROE moderado ({roe:.2f}%)", "neutral")
        elif roe > 5:
            add(-1, f"ROE fraco ({roe:.2f}%) — rentabilidade abaixo do esperado", "negative")
        else:
            add(-2, f"ROE muito baixo ({roe:.2f}%) — empresa pouco rentável", "negative")

    # EV/EBITDA
    if ev_ebitda is not None and ev_ebitda > 0:
        if ev_ebitda < 7:
            add(+1, f"EV/EBITDA atrativo ({ev_ebitda:.2f}x)", "positive")
        elif ev_ebitda > 15:
            add(-1, f"EV/EBITDA elevado ({ev_ebitda:.2f}x) — empresa cara pelo resultado operacional", "negative")

    # Margem Líquida
    if mrg_liq is not None:
        if mrg_liq > 15:
            add(+1, f"Margem Líquida saudável ({mrg_liq:.2f}%)", "positive")
        elif mrg_liq < 0:
            add(-2, f"Margem Líquida negativa ({mrg_liq:.2f}%) — operação com prejuízo", "negative")

    available = sum(1 for v in [p_l, p_vp, dy, roe, ev_ebitda, mrg_liq] if v is not None)
    if available == 0:
        return {"signal": "aguardar", "score": 0, "reasons": [
            {"text": "Nenhum indicador disponível para análise.", "type": "neutral"}
        ]}

    if score >= 5:
        signal = "compra"
    elif score <= -2:
        signal = "venda"
    else:
        signal = "aguardar"

    return {"signal": signal, "score": score, "reasons": reasons}


# ---------------------------------------------------------------------------
# Função pública
# ---------------------------------------------------------------------------
def get_indicators(ticker: str, source: str = "investidor10") -> list[dict]:
    provider = PROVIDERS.get(source)
    if provider is None:
        raise ValueError(f"Provedor desconhecido: '{source}'. Disponíveis: {list(PROVIDERS)}")

    raw = provider["fn"](ticker)

    return [
        {
            "key":         key,
            "label":       meta["label"],
            "description": meta["description"],
            "fmt":         meta["fmt"],
            "value":       raw.get(key),
            "display":     _fmt_value(raw.get(key), meta["fmt"]),
        }
        for key, meta in INDICATORS.items()
    ]
