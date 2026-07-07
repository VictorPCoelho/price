"""Rotas HTTP — camada fina sobre o serviço. Formulários padrão + redirect."""
from datetime import date, datetime
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import db
from app.core.prioridade import STATUS_ROTULOS
from app.web import servico

RAIZ = Path(__file__).resolve().parent

TIPOS_SESSAO = {
    "teoria": "Teoria",
    "questoes": "Questões",
    "lei_seca": "Lei seca",
    "revisao": "Revisão",
    "simulado": "Simulado",
}


def _data_ou_hoje(valor: str | None) -> date:
    if valor:
        try:
            return datetime.strptime(valor, "%Y-%m-%d").date()
        except ValueError:
            pass
    return date.today()


def criar_app() -> FastAPI:
    app = FastAPI(title="Maestro de Estudos")
    app.mount("/static", StaticFiles(directory=RAIZ / "static"), name="static")
    templates = Jinja2Templates(directory=RAIZ / "templates")
    templates.env.filters["hhmm"] = lambda m: f"{m // 60}h{m % 60:02d}"
    templates.env.filters["status_rotulo"] = lambda s: STATUS_ROTULOS.get(s, s)
    templates.env.filters["data_br"] = lambda s: (
        datetime.strptime(s, "%Y-%m-%d").strftime("%d/%m/%Y") if s else "—"
    )

    def render(request: Request, nome: str, **contexto):
        conn = request.state.conn
        contexto.setdefault("concursos", servico.listar_concursos(conn))
        contexto.setdefault("hoje", date.today())
        contexto["status_rotulos"] = STATUS_ROTULOS
        contexto["tipos_sessao"] = TIPOS_SESSAO
        return templates.TemplateResponse(request, nome, contexto)

    @app.middleware("http")
    async def abrir_conexao(request: Request, chamar):
        request.state.conn = db.conectar()
        try:
            return await chamar(request)
        finally:
            request.state.conn.close()

    # ------------------------------------------------------------- concursos
    @app.get("/")
    def raiz(request: Request):
        concurso = servico.concurso_ativo(request.state.conn)
        return RedirectResponse("/painel" if concurso else "/concursos")

    @app.get("/concursos")
    def concursos(request: Request):
        return render(request, "concursos.html", ativo_nav="concursos",
                      concurso=servico.concurso_ativo(request.state.conn))

    @app.post("/concursos")
    def criar_concurso(request: Request, nome: str = Form(...),
                       banca: str = Form(""), data_prova: str = Form("")):
        servico.criar_concurso(request.state.conn, nome, banca, data_prova or None)
        return RedirectResponse("/edital", status_code=303)

    @app.post("/concursos/{concurso_id}/ativar")
    def ativar_concurso(request: Request, concurso_id: int):
        servico.ativar_concurso(request.state.conn, concurso_id)
        return RedirectResponse("/painel", status_code=303)

    # ---------------------------------------------------------------- painel
    @app.get("/painel")
    def painel(request: Request):
        conn = request.state.conn
        concurso = servico.concurso_ativo(conn)
        if not concurso:
            return RedirectResponse("/concursos")
        dados = servico.painel(conn, concurso, date.today())
        return render(request, "painel.html", ativo_nav="painel",
                      concurso=concurso, **dados)

    # ---------------------------------------------------------------- edital
    @app.get("/edital")
    def edital(request: Request):
        conn = request.state.conn
        concurso = servico.concurso_ativo(conn)
        if not concurso:
            return RedirectResponse("/concursos")
        disciplinas = [
            {"disciplina": d, "topicos": servico.listar_topicos(conn, d["id"])}
            for d in servico.listar_disciplinas(conn, concurso["id"])
        ]
        return render(request, "edital.html", ativo_nav="edital",
                      concurso=concurso, disciplinas=disciplinas)

    @app.post("/disciplinas")
    def criar_disciplina(request: Request, concurso_id: int = Form(...),
                         nome: str = Form(...), peso: int = Form(1)):
        servico.criar_disciplina(request.state.conn, concurso_id, nome, peso)
        return RedirectResponse("/edital", status_code=303)

    @app.post("/disciplinas/{disciplina_id}/topicos")
    def adicionar_topicos(request: Request, disciplina_id: int,
                          texto: str = Form(...)):
        servico.adicionar_topicos(request.state.conn, disciplina_id, texto)
        return RedirectResponse("/edital", status_code=303)

    @app.post("/topicos/{topico_id}/status")
    def status_topico(request: Request, topico_id: int, status: str = Form(...)):
        servico.definir_status_topico(request.state.conn, topico_id, status, date.today())
        return RedirectResponse("/edital", status_code=303)

    # ----------------------------------------------------------------- ciclo
    @app.get("/ciclo")
    def ciclo(request: Request):
        conn = request.state.conn
        concurso = servico.concurso_ativo(conn)
        if not concurso:
            return RedirectResponse("/concursos")
        blocos = servico.blocos_do_ciclo(conn, concurso["id"])
        atual = servico.bloco_atual(conn, concurso)
        return render(request, "ciclo.html", ativo_nav="ciclo", concurso=concurso,
                      blocos=blocos, bloco_atual=atual,
                      disciplinas=servico.listar_disciplinas(conn, concurso["id"]))

    @app.post("/ciclo/blocos")
    def criar_bloco(request: Request, concurso_id: int = Form(...),
                    disciplina_id: int = Form(...), duracao_min: int = Form(60)):
        servico.criar_bloco(request.state.conn, concurso_id, disciplina_id, duracao_min)
        return RedirectResponse("/ciclo", status_code=303)

    @app.post("/ciclo/blocos/{bloco_id}/remover")
    def remover_bloco(request: Request, bloco_id: int):
        servico.remover_bloco(request.state.conn, bloco_id)
        return RedirectResponse("/ciclo", status_code=303)

    @app.post("/ciclo/avancar")
    def avancar_ciclo(request: Request, concurso_id: int = Form(...)):
        servico.avancar_ciclo(request.state.conn, concurso_id)
        return RedirectResponse("/ciclo", status_code=303)

    # --------------------------------------------------------- estudar agora
    @app.get("/estudar")
    def estudar(request: Request):
        conn = request.state.conn
        concurso = servico.concurso_ativo(conn)
        if not concurso:
            return RedirectResponse("/concursos")
        rec = servico.recomendar(conn, concurso, date.today())
        return render(request, "estudar.html", ativo_nav="estudar",
                      concurso=concurso,
                      disciplinas=servico.listar_disciplinas(conn, concurso["id"]),
                      **rec)

    # ---------------------------------------------------------------- sessões
    @app.get("/sessoes")
    def sessoes(request: Request):
        conn = request.state.conn
        concurso = servico.concurso_ativo(conn)
        if not concurso:
            return RedirectResponse("/concursos")
        disciplinas = servico.listar_disciplinas(conn, concurso["id"])
        mapa_topicos = {
            str(d["id"]): [
                {"id": t["id"], "titulo": t["titulo"]}
                for t in servico.listar_topicos(conn, d["id"])
            ]
            for d in disciplinas
        }
        return render(request, "sessoes.html", ativo_nav="sessoes",
                      concurso=concurso, disciplinas=disciplinas,
                      mapa_topicos=mapa_topicos,
                      sessoes=servico.listar_sessoes(conn, concurso["id"]))

    @app.post("/sessoes")
    def registrar_sessao(
        request: Request,
        concurso_id: int = Form(...),
        disciplina_id: int = Form(0),
        topico_id: int = Form(0),
        tipo: str = Form("teoria"),
        minutos: int = Form(...),
        data_sessao: str = Form(""),
        paginas: str = Form(""),
        questoes_feitas: str = Form(""),
        questoes_acertadas: str = Form(""),
        obs: str = Form(""),
        teoria_concluida: str = Form(""),
        bloco_concluido: str = Form(""),
        voltar_para: str = Form("/sessoes"),
    ):
        servico.registrar_sessao(
            request.state.conn,
            concurso_id=concurso_id,
            disciplina_id=disciplina_id or None,
            topico_id=topico_id or None,
            tipo=tipo if tipo in TIPOS_SESSAO else "teoria",
            minutos=minutos,
            data_sessao=_data_ou_hoje(data_sessao),
            paginas=int(paginas) if paginas.strip().isdigit() else None,
            questoes_feitas=int(questoes_feitas) if questoes_feitas.strip().isdigit() else None,
            questoes_acertadas=int(questoes_acertadas) if questoes_acertadas.strip().isdigit() else None,
            obs=obs,
            teoria_concluida=bool(teoria_concluida),
            bloco_concluido=bool(bloco_concluido),
        )
        destino = voltar_para if voltar_para.startswith("/") else "/sessoes"
        return RedirectResponse(destino, status_code=303)

    # --------------------------------------------------------------- revisões
    @app.post("/revisoes/{revisao_id}/concluir")
    def concluir_revisao(request: Request, revisao_id: int,
                         resultado: str = Form(...),
                         voltar_para: str = Form("/painel")):
        servico.concluir_revisao(request.state.conn, revisao_id, resultado, date.today())
        destino = voltar_para if voltar_para.startswith("/") else "/painel"
        return RedirectResponse(destino, status_code=303)

    return app


app = criar_app()
