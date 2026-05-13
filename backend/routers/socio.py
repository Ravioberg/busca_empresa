from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from database import get_db
from schemas import SocioListItem, ListaResultados
import crud

router = APIRouter(prefix="/api/v1/socio", tags=["socio"])


@router.get("/perfil")
def perfil_socio(
    response: Response,
    cpf: str | None = Query(None, min_length=3),
    nome: str | None = Query(None, min_length=2),
    db: Session = Depends(get_db),
):
    if not cpf and not nome:
        raise HTTPException(status_code=422, detail="Informe 'cpf' ou 'nome'.")
    response.headers["Cache-Control"] = "public, max-age=300"
    resultado = crud.get_perfil_socio(db, cpf=cpf, nome=nome)
    if not resultado:
        raise HTTPException(status_code=404, detail="Sócio não encontrado.")
    return resultado


@router.get("/busca", response_model=ListaResultados[SocioListItem])
def busca_socio(
    response: Response,
    nome: str | None = Query(None, min_length=2),
    cpf: str | None = Query(None, min_length=3),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    known_total: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    if not nome and not cpf:
        raise HTTPException(status_code=422, detail="Informe 'nome' ou 'cpf'.")
    response.headers["Cache-Control"] = "public, max-age=300"
    if cpf:
        return crud.busca_socio_cpf(db, cpf, skip, limit, known_total=known_total)
    return crud.busca_socio_nome(db, nome, skip, limit, known_total=known_total)
