from fastapi import FastAPI, HTTPException, Query, status, Depends
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate as sqlalchemy_paginate
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

# --- Import e configuração SQLAlchemy aqui ---
# engine, SessionLocal, Base, AtletaModel (classe SQLAlchemy) definidos no seu projeto

app = FastAPI()

# Pydantic model para resposta customizada do atleta (GET all)
class AtletaResponse(BaseModel):
    nome: str
    centro_treinamento: str
    categoria: str

    class Config:
        orm_mode = True

# Dependência para banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/atletas", response_model=Page[AtletaResponse])
def listar_atletas(
    nome: Optional[str] = Query(None),
    cpf: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(AtletaModel)

    if nome:
        query = query.filter(AtletaModel.nome.ilike(f"%{nome}%"))
    if cpf:
        query = query.filter(AtletaModel.cpf == cpf)

    return sqlalchemy_paginate(query)

# Tratamento global para IntegrityError
from fastapi.responses import JSONResponse
from fastapi.requests import Request

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    # Aqui tenta extrair o cpf duplicado da mensagem do erro (depende do banco)
    msg = str(exc.orig)
    cpf_duplicado = "x"  # default, depois tentar extrair do msg real se possível
    if "cpf" in msg:
        # Exemplo de extração, ajuste conforme a mensagem real do seu BD
        import re
        match = re.search(r"\((cpf)\)=\((.*?)\)", msg)
        if match:
            cpf_duplicado = match.group(2)
    return JSONResponse(
        status_code=303,
        content={"detail": f"Já existe um atleta cadastrado com o cpf: {cpf_duplicado}"},
    )

# Configura paginação na aplicação
add_pagination(app)

