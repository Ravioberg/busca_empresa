from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import EmpresaDetalhe, EmpresaListItem, ListaResultados
from .. import crud

# Definição do roteador para endpoints relacionados a empresas
# prefix: todas as rotas aqui começarão com /api/v1/empresa
# tags: agrupa estas rotas na documentação automática (Swagger)
router = APIRouter(prefix="/api/v1/empresa", tags=["empresa"])


@router.get(
    "/busca", 
    response_model=ListaResultados[EmpresaListItem], 
    responses={404: {"description": "Não encontrado"}}
)
def busca_por_nome(
    response: Response,
    # Nome ou Razão Social para busca (mínimo 2 caracteres)
    nome: Annotated[str, Query(min_length=2)],
    # Paginação: quantos registros pular
    skip: Annotated[int, Query(ge=0)] = 0,
    # Paginação: limite de registros por página (máximo 100)
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    # Otimização: se o frontend já sabe o total, evita um COUNT desnecessário no banco
    known_total: Annotated[int, Query(ge=0)] = 0,
    # Injeção de dependência da sessão do banco de dados
    db: Session = Depends(get_db),
):
    """
    Realiza a busca de empresas por Nome Fantasia ou Razão Social.
    Utiliza FTS5 (Full-Text Search) no SQLite para performance instantânea.
    """
    # Define cache no navegador por 5 minutos para evitar requisições repetidas idênticas
    response.headers["Cache-Control"] = "public, max-age=300"
    
    return crud.busca_empresa_nome(db, nome, skip, limit, known_total=known_total)


@router.get(
    "/{cnpj}/rede", 
    responses={404: {"description": "CNPJ não encontrado"}}
)
def busca_rede(cnpj: str, db: Session = Depends(get_db)):
    """
    Retorna a rede de relacionamentos de uma empresa (sócios e outras empresas dos mesmos sócios).
    Útil para visualização de grafos ou análise de grupos econômicos.
    """
    resultado = crud.get_empresa_rede(db, cnpj)
    if not resultado:
        raise HTTPException(status_code=404, detail="CNPJ não encontrado.")
    return resultado


@router.get(
    "/{cnpj}/grafo",
    responses={404: {"description": "CNPJ não encontrado"}}
)
def grafo_empresa(
    cnpj: str,
    # Profundidade de expansão (saltos) a partir da empresa raiz
    profundidade: Annotated[int, Query(ge=1, le=10)] = 2,
    db: Session = Depends(get_db),
):
    """
    Grafo de rede societária (nós planos + arestas) por expansão BFS de N saltos
    a partir da empresa. Empresa → sócios → empresas → sócios → ... (até N).
    """
    resultado = crud.get_grafo_rede(db, cnpj=cnpj, profundidade=profundidade)
    if not resultado:
        raise HTTPException(status_code=404, detail="CNPJ não encontrado.")
    return resultado


@router.get(
    "/{cnpj}", 
    response_model=EmpresaDetalhe, 
    responses={404: {"description": "CNPJ não encontrado na base"}}
)
def busca_por_cnpj(cnpj: str, db: Session = Depends(get_db)):
    """
    Retorna os detalhes completos de uma empresa específica através do seu CNPJ (14 dígitos).
    Inclui dados de endereço, CNAEs, capital social e quadro societário atualizado.
    """
    resultado = crud.get_empresa_by_cnpj(db, cnpj)
    if not resultado:
        raise HTTPException(status_code=404, detail="CNPJ não encontrado na base.")
    return resultado
