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

## 6. Decisões em aberto (para a próxima conversa)

1. **Plataforma**: app web local (Streamlit/Dash — stack que você já domina no projeto de precificação) vs. web hospedado vs. mobile-first? Sugestão inicial: **Streamlit/Dash local com SQLite** — rápido de construir e validar o modelo.
2. **Uso pessoal ou produto?** Muda tudo em autenticação, hospedagem e polimento.
3. **Qual concurso/banca alvo?** (CESPE/Cebraspe, FGV, FCC...) O estilo da banca influencia o modelo (certo/errado vs. múltipla escolha muda a métrica de proficiência).
4. **Banco de questões**: registrar manualmente resultados dos sites (simples) vs. ter questões dentro da ferramenta (muito mais trabalho/conteúdo)?
5. **Revisão**: fixa 24h/7d/30d (simples, previsível) vs. SM-2 adaptativo (melhor, porém mais complexo)?
