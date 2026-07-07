# 🎯 Maestro de Estudos

Ferramenta local de condução de estudos para concursos. Responde a pergunta
central do concurseiro: **"o que eu devo estudar agora?"**

Modelo completo e roadmap: [`docs/BRAINSTORM_FERRAMENTA_ESTUDOS.md`](../docs/BRAINSTORM_FERRAMENTA_ESTUDOS.md).

## Como rodar

```bash
./iniciar.sh        # Linux/Mac
iniciar.bat         # Windows
```

Acesse **http://localhost:8600**. Os dados ficam em `estudos/data/estudos.db`
(SQLite local — fora do git).

## O que já faz (Fatia 1)

- **Edital verticalizado** — cole o trecho do edital e ele vira checklist de
  tópicos com status (não visto → teoria vista → exercitado → dominado).
- **Ciclo de estudos** — sequência circular de blocos por disciplina; terminou
  um bloco, o ponteiro avança. Sem cronograma fixo, sem atraso acumulado.
- **Revisões espaçadas 1/7/30 dias** — agendadas automaticamente ao concluir a
  teoria de um tópico. "Esqueci" reagenda para amanhã; "parcial", para 3 dias.
- **"Estudar agora"** — cascata de decisão: revisões vencidas primeiro; depois
  o bloco do ciclo, com o tópico de maior prioridade
  (peso da disciplina × (1 − proficiência) × urgência da prova × status).
- **Cronômetro + registro de sessão** — tempo líquido, páginas, questões
  feitas/acertadas. Bom desempenho em questões promove o tópico a
  exercitado/dominado automaticamente.
- **Painel** — streak de dias seguidos, horas líquidas por semana, cobertura do
  edital por disciplina, taxa de acerto e fila de revisões.

## Arquitetura

```
app/core/       regras puras (sem UI, sem banco) — 100% testadas
  edital.py       verticalização do texto do edital
  ciclo.py        ponteiro circular do ciclo
  revisao.py      agenda 1/7/30 + reagendamento por resultado
  prioridade.py   motor de score "o que estudar agora"
  estatisticas.py streak, horas/semana, cobertura
app/db.py       esquema SQLite + conexão
app/web/        FastAPI + Jinja (servico.py faz a ponte banco ↔ núcleo)
tests/          unitários do núcleo + fluxo web de ponta a ponta
```

## Testes

```bash
python3 -m pytest tests/
```

## Próximas fatias (ver brainstorm, §10.2)

2. Ingestão de PDFs (Estratégia) + estante + estimador de horas restantes
3. Leitor embutido (PDF.js) com grifos e timer acoplado
4. Extração de questões dos PDFs + baterias + proficiência automática
5. Geração de flashcards + exportação Anki
6. AnkiConnect, mapas mentais, camada de IA
