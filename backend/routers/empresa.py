from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from database import get_db
from schemas import EmpresaDetalhe, EmpresaListItem, ListaResultados
import crud

router = APIRouter(prefix="/api/v1/empresa", tags=["empresa"])


@router.get("/busca", response_model=ListaResultados[EmpresaListItem])
def busca_por_nome(
    response: Response,
    nome: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    known_total: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "public, max-age=300"
    return crud.busca_empresa_nome(db, nome, skip, limit, known_total=known_total)


@router.get("/{cnpj}/rede")
def busca_rede(cnpj: str, db: Session = Depends(get_db)):
    resultado = crud.get_empresa_rede(db, cnpj)
    if not resultado:
        raise HTTPException(status_code=404, detail="CNPJ não encontrado.")
    return resultado


@router.get("/{cnpj}", response_model=EmpresaDetalhe)
def busca_por_cnpj(cnpj: str, db: Session = Depends(get_db)):
    resultado = crud.get_empresa_by_cnpj(db, cnpj)
    if not resultado:
        raise HTTPException(status_code=404, detail="CNPJ não encontrado na base.")
    return resultado
