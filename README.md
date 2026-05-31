# Stock Monitor

Aplicação Django para monitoramento de ativos de renda variável na B3, com análise de indicadores fundamentalistas, backtest de estratégia e geração automatizada de sinais de operação em tempo real.

---

## Funcionalidades

| Aba | Descrição |
|---|---|
| **Ativos** | Cadastro da carteira com ticker, quantidade e preço médio |
| **Status** | Cotação atual, variação, indicadores fundamentalistas e recomendação compra/venda/aguardar |
| **Backtest** | Simulação histórica da estratégia com parâmetros ajustáveis e gráfico interativo |
| **Operações** | Sinais de compra e venda em tempo real com confirmação manual e histórico por ativo |

---

## A Estratégia

### Visão geral

A estratégia combina dois conceitos clássicos de gestão de posição: **trailing stop** (proteção de lucro dinâmica) e **recompra programada** (reentrada após queda). O resultado é um ciclo sistemático de captura de lucros parciais sem abandonar a posição no ativo.

```
Preço sobe → atinge meta mínima → rastreia pico
Preço cai X% do pico → vende parcialmente → aguarda queda Y% do preço de venda
Preço cai Y% → recompra → novo ciclo começa
```

### Parâmetros

| Parâmetro | Descrição | Padrão |
|---|---|---|
| `min_profit_pct` | Lucro mínimo para começar a rastrear o pico (% sobre preço médio) | por ativo |
| `trailing_stop_pct` | Queda máxima tolerada a partir do pico para acionar venda | 3% |
| `min_hold_pct` | Porcentagem mínima da posição a manter em carteira | 60% |
| `buyback_pct` | Queda a partir do preço de venda para acionar recompra | 5% |
| `fee_pct` | Taxa B3 por operação de venda | 0,0305% |

### Passo a passo detalhado

**1. Rastreamento do pico**

O sistema começa a monitorar o pico de preço somente após o lucro atingir `min_profit_pct`. Isso evita acionamentos prematuros em oscilações normais de curto prazo.

```
Se (preço_atual − preço_médio) / preço_médio ≥ min_profit_pct:
    pico = max(pico, preço_atual)
```

**2. Gatilho de venda parcial (trailing stop)**

Quando o preço recua `trailing_stop_pct`% a partir do pico registrado, uma venda parcial é executada.

```
Se preço_atual ≤ pico × (1 − trailing_stop_pct / 100):
    → aciona venda parcial
```

**3. Cálculo da quantidade vendida**

A quantidade vendida é calculada para que a posição remanescente valha, no mínimo, o investimento inicial corrigido pela meta mínima de lucro — garantindo que o capital original continue "protegido" em carteira. Um segundo piso (`min_hold_pct`) assegura que nunca se venda mais do que a fração permitida, independentemente do preço.

```
manter_por_lucro = ceil(investimento_inicial × (1 + min_profit_pct/100) / preço_atual)
manter_por_limite = ceil(quantidade_total × min_hold_pct / 100)
manter = max(manter_por_lucro, manter_por_limite)
vender = quantidade_total − manter
```

**4. Alocação da receita da venda**

O caixa gerado pela venda fica reservado para a recompra correspondente. O gatilho de recompra é calculado automaticamente no momento da venda:

```
gatilho_recompra = preço_venda × (1 − buyback_pct / 100)
```

**5. Recompra independente por ciclo**

Cada venda gera uma ordem de recompra própria e independente. Se o ativo cair mais de `buyback_pct`% em relação ao preço de venda, a recompra é executada — recuperando a quantidade vendida a um preço menor e reduzindo o preço médio da posição.

```
Economia por ciclo = receita_da_venda − custo_da_recompra
Novo preço médio = (cotas_anteriores × preço_médio + cotas_recompradas × preço_recompra)
                   / total_de_cotas
```

Múltiplas vendas parciais podem ter recompras pendentes simultâneas, cada uma com seu próprio gatilho.

---

## Base Teórica e Comparativo com o Mercado

### Trailing Stop — a proteção dinâmica de lucro

O trailing stop é uma das ferramentas mais antigas de gestão de risco. Diferente do stop fixo (que protege contra perda a partir do preço de entrada), o trailing stop **segue o preço para cima** e só aciona a saída quando o preço recua a partir do topo.

É amplamente utilizado por gestores quantitativos, traders de tendência (*trend following*) e nos sistemas de *managed futures*. Fundos como o Millburn Ridgefield e o Man AHL, referências globais em estratégias sistemáticas, usam variações de trailing stop como mecanismo central de saída.

No Brasil, corretoras como XP, Clear, Rico e BTG oferecem ordens de trailing stop em suas plataformas. O problema: a ordem cobre **100% da posição** ou uma quantidade fixa definida manualmente pelo investidor antes da execução. Não há cálculo automático de quanto vender para preservar o capital original em carteira.

### Venda Parcial + Preservação do Capital Original

A ideia de nunca se desfazer completamente de uma posição vencedora está no cerne da filosofia de grandes investidores de longo prazo. Jesse Livermore descrevia como "deixar os lucros correrem" enquanto realizava parcialmente para financiar a própria operação. Peter Lynch, em *One Up on Wall Street*, enfatiza a importância de não vender posições inteiras em ativos de qualidade apenas por uma queda de curto prazo.

A regra `min_hold_pct` implementada aqui formaliza isso: **ao menos 60% da posição permanece em carteira**, garantindo exposição contínua ao ativo. A venda parcial serve para capturar lucro, não para encerrar a tese de investimento.

### Recompra Programada — buy the dip sistematizado

Comprar na queda (*buying the dip*) é intuitivo para qualquer investidor de valor, mas executar isso de forma disciplinada é difícil emocionalmente. Quando um ativo cai, o viés de confirmação leva o investidor a hesitar — "e se cair mais?".

A estratégia resolve isso com um **gatilho pré-definido e automático**: o preço de recompra é calculado no momento da venda, antes de qualquer queda. Não há decisão emocional envolvida na execução.

Esse conceito é usado em estratégias quantitativas como o **grid trading** (compras e vendas a intervalos fixos de preço) e em fundos de rebalanceamento automático, onde o próprio rebalanceamento entre ativos funciona como um "comprar o que caiu e vender o que subiu" sistemático.

### Indicadores Fundamentalistas como Filtro de Qualidade

Antes de operar qualquer estratégia de timing, a aplicação avalia os fundamentos do ativo via Investidor10:

| Indicador | Papel na análise |
|---|---|
| P/L | Filtra ativos caros em relação ao lucro gerado |
| P/VP | Identifica ativos negociando abaixo do valor patrimonial |
| DY | Confirma geração de caixa e distribuição ao acionista |
| ROE | Mede eficiência na geração de lucro sobre o patrimônio |
| EV/EBITDA | Avalia o valuation considerando a dívida líquida |
| Margem Líquida | Qualidade e sustentabilidade do lucro |

Essa combinação de **análise fundamentalista como filtro de entrada** com **estratégia de timing baseada em trailing stop** é o que investidores como Howard Marks (Oaktree) descrevem como "comprar bons ativos nos momentos certos", em vez de aplicar timing sobre qualquer papel independentemente da qualidade do negócio.

---

## O Diferencial: Automação Parcial do que Já Existe

### O que as corretoras oferecem hoje

As principais corretoras brasileiras disponibilizam ferramentas de stop:

- **Stop loss fixo**: vende se cair X% do preço de entrada
- **Stop gain fixo**: vende se subir Y% do preço de entrada
- **Trailing stop**: vende se cair X% do pico — mas sobre 100% da posição, com quantidade definida manualmente pelo investidor

O processo real que o investidor precisa executar manualmente:

1. Definir manualmente quanto quer vender
2. Cadastrar a ordem na corretora
3. Quando a venda é executada, decidir se quer recomprar, quando e quanto
4. Recadastrar tudo para o próximo ciclo

Na prática, **o processo é totalmente manual e depende de disciplina emocional** — especialmente a etapa de recompra, que exige agir num momento em que o ativo está em queda.

### O que o Stock Monitor automatiza

| Corretora tradicional | Stock Monitor |
|---|---|
| Define quantidade manualmente | Calcula automaticamente quanto vender para preservar capital original + `min_hold_pct` |
| Trailing stop sobre 100% da posição | Trailing stop parcial com piso mínimo configurável |
| Recompra: decisão manual após a queda | Gatilho de recompra calculado no momento da venda, monitorado automaticamente a cada hora |
| Um ciclo por vez | Múltiplas ordens de recompra simultâneas — cada venda tem sua própria ordem independente |
| Sem histórico integrado | Histórico completo: lucro capturado, economia nas recompras e resultado consolidado por ativo |

### O fluxo operacional

1. **Verificação horária automática** — o sistema consulta o preço de cada ativo a cada hora em segundo plano
2. **Sinal gerado** — quando os critérios são atingidos, um sinal de VENDA ou RECOMPRA aparece na aba Operações
3. **Confirmação pelo investidor** — o investidor revisa o sinal, insere o preço executado e confirma (ou cancela)
4. **Estado atualizado automaticamente** — posição, preço médio, recompras pendentes e histórico são atualizados
5. **Backtest antes de operar** — o mesmo motor de decisão pode ser simulado em dados históricos para validar os parâmetros antes de usar com dinheiro real

O sistema é **semi-automatizado por design**: a execução da ordem ainda passa pelo investidor (que a insere na corretora), mas toda a inteligência de *quando agir*, *quanto vender* e *quando recomprar* é calculada e monitorada automaticamente.

---

## Stack Técnica

| Componente | Tecnologia |
|---|---|
| Backend | Django 5.x + PostgreSQL |
| Cotações em tempo real | yfinance (Yahoo Finance) |
| Indicadores fundamentalistas | Web scraping — Investidor10 |
| Dados históricos para backtest | yfinance |
| Verificação automática horária | Thread daemon via `AppConfig.ready()` |
| Frontend | Bootstrap 5 + Chart.js |
| Infraestrutura | Docker + Docker Compose |

---

## Instalação

```bash
git clone https://github.com/alavorato/stockmonitor.git
cd stockmonitor
sudo docker-compose up -d
sudo docker-compose exec web python manage.py migrate
sudo docker-compose exec web python manage.py createsuperuser
```

Acesse `http://localhost:8000`.

---

## Execução manual da verificação

```bash
sudo docker-compose exec web python manage.py check_operations
```

Útil para testar fora do ciclo horário automático ou para verificar o estado atual da carteira imediatamente.
