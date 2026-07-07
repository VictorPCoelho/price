# Brainstorm — Ferramenta de Condução de Estudos para Concursos

> Documento de brainstorm. Objetivo: definir a lógica do modelo antes de construir qualquer coisa.
>
> **Status**: Fatia 1 construída em [`estudos/`](../estudos/README.md) (edital verticalizado,
> ciclo, sessões com cronômetro, revisões 1/7/30 e "estudar agora").

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

### 6.6 Colocar os PDFs dentro da ferramenta — ingestão e armazenamento

A ferramenta passa a ser **a estante única do material**: aulas do Estratégia, mapas da Lulu, editais, lei seca — tudo entra pelo mesmo funil.

**Pipeline de ingestão (o funil):**

```
1. ENTRADA     arrastar-e-soltar na tela  OU  pasta monitorada
               (ex.: ~/Concurso/PDFs — salvou o download lá, a ferramenta ingere sozinha)
2. DEDUP       hash do arquivo → não importa duas vezes a mesma aula/versão
3. METADADOS   nome do arquivo + capa do PDF → detectar curso, disciplina, nº da aula
               (PDFs do Estratégia têm padrão de nome/capa consistente)
4. CLASSIFICAR tipo do material: aula | resumo | mapa mental | edital | lei seca | simulado
5. VÍNCULO     sumário do PDF × edital verticalizado → sugestão automática de
               "aula 04 cobre os tópicos 3.1, 3.2 e 3.4" (usuário confirma/ajusta)
6. INDEXAR     texto por página (busca) + embeddings (RAG) + extração de questões (§6.3)
7. PRONTO      aula aparece na estante com: tópicos vinculados, nº de páginas,
               nº de questões extraídas, custo estimado em horas (§8)
```

**Armazenamento — local por padrão, por três razões:**

- **Licença**: os PDFs têm marca d'água nominal do assinante; mantê-los na máquina do usuário (filesystem + SQLite para metadados/anotações) evita qualquer zona cinzenta de re-hospedagem em nuvem.
- **Tamanho**: uma aula tem 5–20 MB; um curso completo, 1–2 GB. Trivial em disco local, caro e lento para subir em nuvem.
- **Simplicidade**: casa com o MVP Streamlit/Dash + SQLite. Duas opções de guarda: *copiar* para a biblioteca da ferramenta (organização garantida) ou *referenciar no lugar* (o arquivo fica onde está; a ferramenta só indexa). Sugestão: copiar — evita links quebrados.

**Leitor embutido (viabilidade real):**

- **PDF.js** (o leitor do Firefox, open source) embute em qualquer app web — funciona em Dash/Streamlit via componente. Renderiza fiel, com zoom, busca e navegação por sumário.
- **Grifos e notas como camada separada**: as anotações são salvas no banco (página + coordenadas + cor + texto), **nunca alterando o PDF original**. Vantagens: o arquivo fica intacto (re-download/atualização de versão não perde nada), os grifos são consultáveis como dados ("todos os meus grifos de Atos Administrativos") e viram matéria-prima de cards (§7.1).
- **Retomada automática**: a ferramenta guarda página e posição por aula — "continuar de onde parei" é um clique a partir da tela "estudar agora".
- **Fallback OCR**: se algum material vier escaneado (raro no Estratégia), `ocrmypdf`/Tesseract entra no passo 6 do funil.

**Backup**: exportar/importar a biblioteca inteira (PDFs + banco de anotações + progresso) num zip — proteção contra troca de máquina.

### 6.7 O fluxo da jornada com o material integrado

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

## 8. "Quanto falta?" — estimativa de horas até o objetivo

Sim, dá para estimar — e esse deveria ser **o número central do dashboard**, porque responde a pergunta emocional do concurseiro: *"vou conseguir chegar lá a tempo?"*

### 8.1 A lógica do estimador

Cada tópico pendente tem um **custo estimado em horas**, decomposto pelo que falta na máquina de estados:

```
custo(tópico) =
    horas_teoria     = páginas restantes ÷ velocidade de leitura (págs/h)
  + horas_questões   = questões alvo × tempo médio por questão
  + horas_revisão    = ~15–20% do acumulado (revisões 1d/7d/30d são curtas, mas existem)

horas_restantes(objetivo) = Σ custo(tópicos pendentes no escopo do objetivo)
```

O "objetivo" é configurável: fechar o edital inteiro, fechar uma disciplina, ou levar um conjunto de tópicos à proficiência ≥ 80%.

### 8.2 Frio no começo, preciso com o uso (o pulo do gato)

- **Dia zero**: usa defaults calibrados (ex.: ~10 págs/h para teoria densa de PDF do Estratégia, ~25 questões/h) e o total de páginas extraído dos PDFs importados → já sai uma estimativa honesta na primeira semana.
- **Com o uso**: cada sessão registrada refina os parâmetros **pessoais e por disciplina** (média móvel): sua velocidade em Direito Administrativo não é a mesma que em Raciocínio Lógico. A estimativa converge para a *sua* realidade.

### 8.3 Confronto com a capacidade — a conta que ninguém quer fazer (e a ferramenta faz)

```
capacidade = horas líquidas/semana (medidas, não prometidas) × semanas até a prova

se horas_restantes > capacidade  →  MODO REALISTA:
```

Quando não cabe, a ferramenta não mente — ela **sugere cortes com base no score de prioridade**:
- trocar aula completa por resumo/mapa mental nas disciplinas de score baixo;
- reduzir o alvo de questões em tópicos de baixa frequência na banca;
- mostrar o trade-off: "cortando X e Y, a projeção passa a caber com 2 semanas de folga".

Visualização: **burndown chart** (horas restantes × tempo, como em sprint) com a linha da data da prova. A cada semana o gráfico mostra se o ritmo real sustenta a meta.

---

## 9. Benchmark e complementos: Estudei e Mapas da Lulu

### 9.1 Estudei ([estudei.com.br](https://estudei.com.br/)) — o que validar e copiar

O Estudei é hoje a referência comercial de *gestão* de estudos: ciclo com matérias verticalizadas, cronograma automático adaptado ao ritmo, revisões programadas, registro de horas/páginas/aulas, indicadores de constância e **mapa de dificuldades × facilidades**. Dois detalhes deles valem incorporar:

1. **Streak de constância com "check" diário** — cada dia planejado e cumprido rende um check; pular quebra a sequência. Gamificação mínima e eficaz (mesma mecânica do Duolingo). Encaixa direto no nosso dashboard de constância.
2. **Registro em múltiplas unidades** (horas, páginas lidas, aulas assistidas) — nosso modelo de sessão já prevê tempo e páginas; vale acrescentar "aulas/vídeos" como unidade.

**O que o Estudei NÃO faz (nosso diferencial)**: ele gerencia *agenda*, mas não *entende o conteúdo*. Não lê os PDFs, não extrai questões, não gera cards, não tem camada de IA, não fecha o ciclo com o Anki. Nossa ferramenta é "Estudei + cérebro sobre o material".

### 9.2 Mapas da Lulu ([mapasdalulu.com.br](https://mapasdalulu.com.br/)) — mapas mentais como ativo de revisão

Os Mapas da Lulu (≈1.900 mapas, 40+ disciplinas, com mnemônicos, lei seca, jurisprudência e pegadinhas) são material de **revisão rápida** — o complemento perfeito para as revisões 1d/7d/30d, onde reler o PDF inteiro é inviável. Integrações possíveis:

1. **Mapas como ativo vinculado ao tópico**: importar os PDFs dos mapas comprados e vinculá-los ao edital verticalizado, igual às aulas. Na hora da revisão, a ferramenta abre o mapa do tópico (não a aula de 150 páginas).
2. **Mapa → Anki via image occlusion**: ocultar ramos do mapa mental vira um card visual poderoso (seção 7.1). Um mapa rende dezenas de cards.
3. **Geração automática de mapas** (fase 3): o LLM gera um mapa mental do tópico a partir do resumo do PDF do Estratégia (saída em Markmap/Mermaid, renderizável na própria ferramenta). Você teria "Mapas da Lulu automáticos" do seu próprio material — e os da Lulu como padrão-ouro de qualidade/formato a imitar.
4. **Modo véspera de prova**: sequência só de mapas + flashcards com maior taxa de lapso, ordenada por score de prioridade.

---

## 10. Arquitetura recomendada e estratégia de construção

### 10.1 A decisão: web app leve, não Streamlit

**Streamlit descartado** (com dor no coração, pela velocidade): duas peças centrais brigam com o modelo dele —

- **Leitor de PDF com grifos**: exige camada de anotação por coordenadas sobre o PDF.js. No Streamlit isso é gambiarra dentro de iframe, frágil e sem acesso decente aos eventos de seleção de texto.
- **Timer de sessão**: o Streamlit re-executa o script inteiro a cada clique; manter um cronômetro rodando enquanto o usuário lê é nadar contra a corrente.
- Triagem rápida de cards (aprovar/editar/descartar em sequência) também sofre com o modelo de rerun.

Começar em Streamlit = reescrever tudo na fase 2. Melhor não pagar esse pedágio.

**Recomendação: FastAPI + Jinja + HTMX + PDF.js** — um web app de verdade, mas com o mínimo de JavaScript:

| Camada | Tecnologia | Por quê |
|---|---|---|
| Núcleo (engine) | **Pacote Python puro** + SQLite | Toda a inteligência (parser de PDF, motor de prioridade, estimador, agendador de revisões, gerador de cards) vive aqui, **sem nenhuma dependência de UI**. 100% testável. |
| API | **FastAPI** | Fina — só expõe o núcleo. |
| Interface | **Jinja + HTMX + Alpine.js** | Interatividade de app (timer, triagem, atualizações parciais) escrevendo ~95% Python/HTML. Sem build de frontend, sem React para manter. |
| Leitor | **PDF.js** + overlay de anotações | Integra nativamente numa página web; os grifos são eventos JS salvos via API. |

Roda local (`localhost`), single-user, um comando para subir — mesmo modelo dos `iniciar.sh` do projeto de precificação.

### 10.2 Estratégia anti-"monte de processo mal formulado"

O risco real de um projeto desses não é a tecnologia — é acumular features 80% prontas. Antídotos, que valem como contrato de construção:

1. **Fatias verticais, não camadas horizontais.** Cada fatia entrega um fluxo completo, usável no seu estudo real no mesmo dia, antes de começar a próxima:
   - **Fatia 1**: edital verticalizado + ciclo + registro de sessão + "estudar agora" + revisões 1d/7d/30d. *(Já dá para estudar com a ferramenta.)*
   - **Fatia 2**: ingestão de PDFs + estante + progresso de leitura + estimador de horas (§8).
   - **Fatia 3**: leitor embutido com grifos + timer acoplado.
   - **Fatia 4**: extração de questões + baterias + proficiência alimentando o score.
   - **Fatia 5**: geração de cards + exportação Anki.
   - **Fatia 6+**: AnkiConnect de volta, mapas mentais, camada de IA.
2. **O núcleo é testado contra os SEUS PDFs.** O parser (sumário, questões, metadados) é o ponto com maior risco de "alucinação"; ele nasce com testes dourados sobre aulas reais do Estratégia: *"desta aula 04, extrair 47 questões e este sumário"*. Parser que não passa no teste não entra.
3. **Heurística conservadora: na dúvida, perguntar — nunca inventar.** Se a extração não tem confiança (sumário estranho, questão mal delimitada), a ferramenta marca "revisar manualmente" em vez de registrar dado errado. Dado ruim no motor de prioridade envenena tudo que vem depois.
4. **Critério de pronto por fatia**: você usou no estudo real por alguns dias e não voltou para a planilha. Só então a próxima fatia começa.
5. **Uma base SQLite local, com backup em zip desde a fatia 1.** Seus dados de estudo nunca ficam reféns de refatoração.

---

## 11. Decisões em aberto (para a próxima conversa)

1. **Plataforma**: ~~Streamlit/Dash vs. web~~ → **DECIDIDO (§10): web app local — FastAPI + Jinja + HTMX + PDF.js, núcleo em pacote Python puro com SQLite.** Streamlit bateria no teto no leitor de PDF com grifos e no timer de sessão.
2. **Uso pessoal ou produto?** Muda tudo em autenticação, hospedagem e polimento.
3. **Qual concurso/banca alvo?** (CESPE/Cebraspe, FGV, FCC...) O estilo da banca influencia o modelo (certo/errado vs. múltipla escolha muda a métrica de proficiência).
4. **Banco de questões**: ~~registrar manualmente vs. questões internas~~ → em boa parte resolvido pela extração das questões comentadas dos PDFs do Estratégia (seção 6.3). Resta decidir se também registramos baterias feitas fora (QConcursos/TEC) de forma manual.
5. **Revisão**: fixa 24h/7d/30d (simples, previsível) vs. SM-2 adaptativo (melhor, porém mais complexo)?
6. **Leitor de PDF**: embutido na ferramenta (sessão automática, grifos integrados — mais trabalho de construir) vs. ler fora e registrar só o progresso (MVP mais rápido)?
7. **Flashcards**: exportar para o Anki (`.apkg`/AnkiConnect — esforço baixo, app mobile pronto) vs. revisão espaçada interna com FSRS (experiência unificada, mais trabalho)? Sugestão: Anki primeiro, interno depois.
8. **Mapas mentais**: só importar/vincular os da Lulu (simples) vs. também gerar mapas automáticos com LLM (Markmap/Mermaid) a partir dos resumos?
9. **Estimador de horas**: qual objetivo padrão exibir no dashboard — fechar o edital, fechar a disciplina atual, ou proficiência ≥ 80% nos tópicos de maior peso?
