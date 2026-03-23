# Como executar / publicar o app

## Opção 1 — Local (mais rápido)

```bash
# 1. Instala dependências
pip install -r requirements.txt

# 2. Roda
streamlit run app.py

# 3. Acessa: http://localhost:8501
```

## Opção 2 — Streamlit Community Cloud (gratuito, acesso via link)

1. Crie conta em https://streamlit.io/cloud
2. Crie repositório no GitHub e suba esta pasta
3. No Streamlit Cloud: "New app" → conecta o repo → seleciona `app.py`
4. Em ~2 minutos o app estará disponível em `https://seu-app.streamlit.app`

## Opção 3 — Docker (servidor interno)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

```bash
docker build -t precificacao-if .
docker run -p 8501:8501 precificacao-if
```

## Adicionar produto novo

1. Edite `recipe.py` — adicione uma nova entrada em `RECEITAS`
2. O app recarrega automaticamente no próximo acesso
