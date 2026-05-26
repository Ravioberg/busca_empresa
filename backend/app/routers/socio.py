from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import SocioListItem, ListaResultados
from .. import crud

# Definição do roteador para endpoints relacionados a sócios
# prefix: todas as rotas aqui começarão com /api/v1/socio
# tags: agrupa estas rotas na documentação automática (Swagger)
router = APIRouter(prefix="/api/v1/socio", tags=["socio"])


@router.get(
    "/perfil", 
    responses={404: {"description": "Sócio não encontrado"}, 422: {"description": "Erro de validação"}}
)
def perfil_socio(
    response: Response,
    # CPF parcial ou completo do sócio
    cpf: Annotated[str | None, Query(min_length=3)] = None,
    # Nome completo ou parcial do sócio
    nome: Annotated[str | None, Query(min_length=2)] = None,
    # Injeção de dependência da sessão do banco de dados
    db: Session = Depends(get_db),
):
    """
    Retorna o perfil detalhado de um sócio, incluindo todas as empresas onde ele
    tem ou já teve participação, capital acumulado e rede de contatos.
    """
    # Validação manual: pelo menos um dos campos deve ser preenchido
    if not cpf and not nome:
        raise HTTPException(status_code=422, detail="Informe 'cpf' ou 'nome'.")
    
    # Cache de 5 minutos para performance
    response.headers["Cache-Control"] = "public, max-age=300"
    
    resultado = crud.get_perfil_socio(db, cpf=cpf, nome=nome)
    if not resultado:
        raise HTTPException(status_code=404, detail="Sócio não encontrado.")
    return resultado


@router.get(
    "/busca", 
    response_model=ListaResultados[SocioListItem], 
    responses={422: {"description": "Erro de validação"}}
)
def busca_socio(
    response: Response,
    # Nome para busca (mínimo 2 caracteres)
    nome: Annotated[str | None, Query(min_length=2)] = None,
    # CPF para busca (mínimo 3 caracteres)
    cpf: Annotated[str | None, Query(min_length=3)] = None,
    # Paginação: registros para pular
    skip: Annotated[int, Query(ge=0)] = 0,
    # Paginação: limite por página
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    # Otimização para evitar recontagem no banco
    known_total: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
):
    """
    Busca simplificada de sócios para listagem inicial.
    Diferencia automaticamente busca por Nome ou CPF.
    """
    if not nome and not cpf:
        raise HTTPException(status_code=422, detail="Informe 'nome' ou 'cpf'.")
    
    response.headers["Cache-Control"] = "public, max-age=300"
    
    # Prioriza busca por CPF se fornecido, caso contrário busca por nome
    if cpf:
        return crud.busca_socio_cpf(db, cpf, skip, limit, known_total=known_total)
    return crud.busca_socio_nome(db, nome, skip, limit, known_total=known_total)
