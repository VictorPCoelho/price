# Brainstorm — Ferramenta de Condução de Estudos para Concursos

> Documento de brainstorm. Objetivo: definir a lógica do modelo antes de construir qualquer coisa.

---

## 1. O que os aprovados realmente usam (e por quê funciona)

Olhando o que é consenso entre aprovados e coaches de concurso, o "kit vencedor" se resume a 5 pilares:

| Pilar | Ferramenta típica | Por que funciona |
|---|---|---|
| **Estudo por questões** | QConcursos, TEC Concursos | Prática ativa (active recall) supera releitura passiva. Estudar pela banca revela o padrão de cobrança. |
| **Revisão espaçada** | Anki, revisões 24h/7d/30d | Combate a curva do esquecimento. É o fator nº 1 de retenção a longo prazo. |
| **Ciclo de estudos** | Planilha (método Alexandre Meirelles) | Diferente de cronograma fixo por dia, o ciclo é uma sequência de blocos por matéria: estudou um bloco, avança para o próximo, sem "atraso" acumulado. Resiliente à vida real. |
| **Edital verticalizado** | Planilha/checklist | Transforma o edital em lista de tópicos com status (visto, revisado, exercitado). Dá visão de cobertura e evita pontos cegos. |
| **Métricas de constância** | Planilhas, apps de pomodoro | Horas *líquidas* por semana e taxa de acerto por tópico. Aprovação vem de constância medida, não de maratonas. |

O problema: hoje isso vive espalhado em 4–5 ferramentas desconectadas (planilha + Anki + site de questões + PDF do edital + timer). **A oportunidade da ferramenta é ser o "maestro" que integra esses pilares num único fluxo.**

---

## 2. A pergunta central que a ferramenta responde

> **"O que eu devo estudar AGORA, por quanto tempo, e como está minha real chance de cobertura do edital?"**

Tudo no modelo existe para responder isso. O usuário não deveria planejar; ele abre a ferramenta e ela diz o próximo bloco.

---

## 3. Lógica do modelo (entidades)

```
Concurso (edital, banca, data da prova)
 └── Disciplina (peso na prova, nº de questões)
      └── Tópico (item do edital verticalizado)
           ├── status: não visto | teoria vista | exercitado | dominado
           ├── proficiência: taxa de acerto em questões (0–100%)
           └── agenda de revisões (spaced repetition)

CicloDeEstudos
 └── Bloco (disciplina, duração alvo, ordem)   ← ponteiro circular: terminou, avança

SessãoDeEstudo (o registro atômico)
 ├── data, tópico, tempo líquido
 ├── tipo: teoria | questões | lei seca | revisão | simulado
 └── resultado: questões feitas / acertadas

Revisão (gerada automaticamente ao concluir teoria de um tópico)
 └── vencimentos: +1d, +7d, +30d  (ou algoritmo SM-2 adaptativo)
```

### Motor de decisão — "o que estudar agora"

Prioridade em cascata:

1. **Revisões vencidas** — sempre primeiro (são curtas e é onde mora a retenção).
2. **Próximo bloco do ciclo** — a disciplina apontada pelo ponteiro do ciclo.
3. **Dentro da disciplina, qual tópico?** — ranking por score de prioridade:

```
score(tópico) = peso_disciplina × frequência_na_banca × (1 − proficiência) × urgência(data_da_prova)
```

- `peso_disciplina`: nº de questões da matéria na prova ÷ total
- `frequência_na_banca`: quão cobrado o tópico é (começa uniforme; refina com dados)
- `proficiência`: taxa de acerto recente do usuário no tópico
- `urgência`: perto da prova, o modelo desloca o mix de teoria → questões/revisão

Ou seja: **matéria que vale muito + tópico muito cobrado + onde você vai mal = topo da fila.**

### Máquina de estados do tópico

```
não visto → teoria vista → exercitado → dominado
                 ↑ (proficiência cai ou revisão falha → regride)
```

Um tópico só é "dominado" com taxa de acerto ≥ X% (ex.: 80%) e revisões em dia. Isso evita a ilusão do "já estudei isso".

---

## 4. Dashboard (as métricas que importam)

- **Cobertura do edital**: % de tópicos por status, por disciplina — e projeção de "com o ritmo atual, você fecha o edital em N semanas" (antes ou depois da prova?).
- **Horas líquidas** por semana + streak de constância.
- **Taxa de acerto** por disciplina/tópico com tendência (melhorando/piorando).
- **Fila de revisões** de hoje (o mais acionável de todos).
- **Mapa de calor** de pontos fracos: peso alto × proficiência baixa = vermelho.

---

## 5. Roadmap sugerido (do mais simples ao mais ambicioso)

**Fase 1 — MVP (o maestro):**
- Cadastro do edital verticalizado (colar texto do edital e quebrar em tópicos).
- Ciclo de estudos configurável.
- Registro de sessões (timer + tempo líquido).
- Revisões automáticas 24h/7d/30d.
- Tela "o que estudar agora" + dashboard básico.

**Fase 2 — Questões e inteligência:**
- Registro de baterias de questões por tópico (feitas nos sites, anotadas aqui) → proficiência alimenta o score.
- Algoritmo de revisão adaptativo (SM-2: acertou fácil → intervalo cresce; errou → volta).
- Simulados com análise de desempenho.

**Fase 3 — IA e automação:**
- LLM para: verticalizar o edital automaticamente a partir do PDF, gerar flashcards e questões inéditas a partir do material, explicar erros.
- Estatísticas de banca (tópicos mais cobrados historicamente).

---

## 6. Integração com o material (PDFs do Estratégia Concursos)

Os PDFs do Estratégia têm uma estrutura previsível — teoria em seções numeradas, **questões comentadas ao final**, resumo/esquemas, sumário navegável — e isso os torna excelentes para automação. A ferramenta deixa de ser só um "maestro de agenda" e passa a entender o conteúdo da jornada.

> Nota: uso estritamente pessoal. Os PDFs têm marca d'água nominal; nada de redistribuir conteúdo — a ferramenta processa localmente, para o próprio assinante.

### 6.1 Biblioteca de materiais (a base de tudo)

- Importar os PDFs e **vincular cada aula aos tópicos do edital verticalizado** (o sumário do PDF ajuda a mapear automaticamente).
- Rastrear **progresso de leitura**: página onde parou, % concluído por aula e por tópico.
- Medir **velocidade de leitura** (páginas líquidas/hora) → a projeção "você fecha o edital em N semanas" deixa de ser chute e vira dado real. Com cursos do Estratégia somando milhares de páginas, isso responde a pergunta crítica: **"leio tudo ou vou de resumo em quais matérias?"**

### 6.2 Leitor integrado com sessão automática

- Abrir o PDF dentro da ferramenta com timer acoplado: a sessão de estudo se registra sozinha (tópico, tempo líquido, páginas lidas). Elimina o atrito de registrar manualmente — atrito é o que mata o uso de planilha.
- **Grifos e notas** vinculados ao tópico. Na revisão, em vez de reler 150 páginas, a ferramenta monta a "versão grifada" da aula.

### 6.3 Extração automática de valor do PDF

- **Questões comentadas → banco interno**: extrair as questões do final de cada aula e transformá-las em baterias respondíveis na ferramenta. Isso resolve a decisão nº 4 (banco de questões) de graça: o Estratégia já entrega centenas de questões por aula, com gabarito e comentário. Cada bateria alimenta a proficiência do tópico no motor de prioridade.
- **Resumos e esquemas → material de revisão**: a seção de resumo do PDF vira o conteúdo padrão das revisões 24h/7d/30d.

### 6.4 Camada de IA sobre o material (fase 3, mas é onde brilha)

- **Teste de saída**: ao fechar uma sessão de leitura, o LLM gera 5 perguntas de recall ativo sobre exatamente o trecho lido. Estudo passivo vira ativo no ato.
- **Flashcards automáticos** dos trechos grifados → deck de revisão espaçada sem esforço manual.
- **"Pergunte ao material"** (RAG sobre os PDFs indexados): "onde o material fala de X?", "explica esse parágrafo com um exemplo", "qual a diferença entre A e B segundo a aula 03?".
- **Verticalização automática**: colar o PDF do edital e o LLM monta a árvore de tópicos e sugere o vínculo com as aulas.

### 6.5 Viabilidade técnica (resumo)

- Extração de texto/sumário/questões: `PyMuPDF` ou `pdfplumber` — os PDFs do Estratégia são texto nativo (não imagem), o que torna isso confiável.
- Questões têm padrão visual/textual consistente (enunciado, alternativas, gabarito comentado) → parsing por regex/heurística cobre a maioria; LLM cobre o resto.
- RAG local: embeddings + SQLite/Chroma; chamadas de LLM via API só quando o usuário pede.

### 6.6 O fluxo da jornada com o material integrado

```
1. Ferramenta diz: "agora: Direito Administrativo — Atos Administrativos (aula 04, pág. 37)"
2. Abre o leitor, timer roda, você grifa. Fecha → sessão registrada sozinha.
3. Teste de saída: 5 perguntas sobre o que acabou de ler.
4. Bateria com as questões comentadas extraídas da própria aula → proficiência atualizada.
5. Revisões +1d/+7d/+30d agendadas usando o resumo do PDF + seus grifos + flashcards.
6. Dashboard reprojeta a data de conclusão do edital com sua velocidade real de leitura.
```

---

## 7. Anki e flashcards — muito além de "gerar cards"

O Anki é a melhor ferramenta de revisão espaçada que existe, e brigar com ele seria burrice. A estratégia é: **a ferramenta vira uma fábrica de cards de alta qualidade + um consumidor das estatísticas do Anki**, fechando o ciclo com o motor de prioridade.

### 7.1 Fontes automáticas de cards (o quê vira card)

| Fonte | Tipo de card | Exemplo |
|---|---|---|
| **Questões erradas** | Básico (frente/verso) | Frente: enunciado da questão que você errou. Verso: gabarito + comentário do professor extraído do PDF. É o card de maior valor: nasce exatamente do seu ponto fraco. |
| **Lei seca** | **Cloze (lacunas)** | "Art. 37: A administração pública obedecerá aos princípios de {{c1::legalidade}}, {{c2::impessoalidade}}..." — cloze é o formato ideal para literalidade, que é o que as bancas cobram. |
| **Grifos na leitura** | Básico ou cloze | Cada grifo vira candidato a card; o LLM reformula como pergunta. |
| **Resumos/esquemas do PDF** | **Image occlusion** | Tabelas e esquemas do Estratégia com partes ocultadas — excelente para comparações (ex.: cargo × emprego × função). |
| **Teste de saída** | Básico | As perguntas de recall que você errou ao fim da sessão de leitura entram direto no deck. |
| **Súmulas/jurisprudência** | Cloze | "Súmula Vinculante {{c1::13}}: veda o {{c2::nepotismo}}..." |
| **Estilo da banca** | Certo/errado | Para CESPE: cards no formato da prova — afirmação, e o verso diz CERTO/ERRADO e por quê. Treina o formato real. |

### 7.2 Qualidade dos cards (onde o LLM ganha o jogo)

Card ruim é pior que card nenhum — vira ruído na fila de revisão. Regras que o gerador aplicaria (princípios do SuperMemo/Piotr Woźniak):

- **Atomicidade**: 1 fato por card. O LLM quebra um parágrafo grifado em 3 cards atômicos, não 1 card-parede-de-texto.
- **Formulação ativa**: sempre pergunta, nunca "leia e lembre".
- **Listas viram cloze sequencial** ou perguntas de contagem ("quantos são os princípios expressos do art. 37?").
- **Mnemônicos**: o LLM sugere um (ex.: LIMPE) no verso quando a lista é decorável.
- **Contexto no rodapé**: todo card carrega a fonte (aula 04, pág. 37, tópico do edital) — um clique volta ao material original.
- **Deduplicação**: antes de criar, verificar por similaridade (embeddings) se já existe card equivalente no deck.
- **Revisão humana em lote**: o LLM propõe, você aprova/edita/descarta numa tela de triagem rápida (swipe). Nada entra no deck sem aprovação — mantém a confiança no deck.

### 7.3 Integração técnica com o Anki

Duas vias, complementares:

1. **Exportação `.apkg`** (biblioteca `genanki`, Python): gera decks prontos para importar. Simples, funciona offline, zero dependência.
2. **AnkiConnect** (API local do Anki desktop): a via rica —
   - cria/atualiza cards direto no Anki, sem exportar/importar;
   - organiza decks espelhando o edital (`Concurso::Direito Adm::Atos Administrativos`) com tags automáticas por disciplina/tópico/aula;
   - **lê as estatísticas de volta**: lapsos, ease, cards maduros vs. jovens por tag.

### 7.4 Fechando o ciclo: Anki → motor de prioridade

Este é o diferencial que nenhuma ferramenta faz hoje:

```
lapsos no Anki no tópico X  →  proficiência(X) cai  →  score de prioridade sobe
→  ferramenta sugere: revisitar teoria / nova bateria de questões do tópico X
```

Ou seja: o Anki deixa de ser um silo de memorização e vira **sensor de retenção** do sistema. Se você está esquecendo Atos Administrativos (muitos lapsos), o motor detecta antes da prova — não na prova.

### 7.5 Alternativa: revisão interna com FSRS

O algoritmo moderno do Anki (FSRS) é open source e tem implementação em Python (`fsrs`). Dá para ter a revisão espaçada **dentro da própria ferramenta**, sem depender do Anki. Trade-off:

- **A favor do Anki**: app mobile maduro, sincronização, o usuário revisa na fila do banco; ecossistema testado.
- **A favor do interno**: experiência unificada, estatísticas nativas, cards de questões podem ser interativos (responder alternativa, não só "lembrei/não lembrei").
- **Sugestão**: começar exportando para o Anki (esforço baixo, valor imediato) e avaliar revisão interna com FSRS depois.

---

## 8. Decisões em aberto (para a próxima conversa)

1. **Plataforma**: app web local (Streamlit/Dash — stack que você já domina no projeto de precificação) vs. web hospedado vs. mobile-first? Sugestão inicial: **Streamlit/Dash local com SQLite** — rápido de construir e validar o modelo.
2. **Uso pessoal ou produto?** Muda tudo em autenticação, hospedagem e polimento.
3. **Qual concurso/banca alvo?** (CESPE/Cebraspe, FGV, FCC...) O estilo da banca influencia o modelo (certo/errado vs. múltipla escolha muda a métrica de proficiência).
4. **Banco de questões**: ~~registrar manualmente vs. questões internas~~ → em boa parte resolvido pela extração das questões comentadas dos PDFs do Estratégia (seção 6.3). Resta decidir se também registramos baterias feitas fora (QConcursos/TEC) de forma manual.
5. **Revisão**: fixa 24h/7d/30d (simples, previsível) vs. SM-2 adaptativo (melhor, porém mais complexo)?
6. **Leitor de PDF**: embutido na ferramenta (sessão automática, grifos integrados — mais trabalho de construir) vs. ler fora e registrar só o progresso (MVP mais rápido)?
7. **Flashcards**: exportar para o Anki (`.apkg`/AnkiConnect — esforço baixo, app mobile pronto) vs. revisão espaçada interna com FSRS (experiência unificada, mais trabalho)? Sugestão: Anki primeiro, interno depois.
