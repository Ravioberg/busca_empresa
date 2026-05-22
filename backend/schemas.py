from pydantic import BaseModel
from typing import List, Optional, Generic, TypeVar

T = TypeVar("T")


class QualificacaoItem(BaseModel):
    codigo: Optional[str] = None
    descricao: Optional[str] = None
    data_entrada: Optional[str] = None
    saiu_em: Optional[str] = None  # YYYY-MM do último mês em que apareceu; None se ainda ativo

    model_config = {"from_attributes": True}


class SocioCompleto(BaseModel):
    nome_socio: Optional[str] = None
    cpf_cnpj_socio: Optional[str] = None
    identificador: Optional[str] = None
    faixa_etaria: Optional[str] = None
    ativo: bool
    qualificacao_atual: Optional[QualificacaoItem] = None
    qualificacoes_anteriores: List[QualificacaoItem] = []

    model_config = {"from_attributes": True}


class CnaeItem(BaseModel):
    codigo: Optional[str] = None
    descricao: Optional[str] = None

    model_config = {"from_attributes": True}


class FilialItem(BaseModel):
    cnpj_completo: Optional[str] = None
    cnpj_completo_formatado: Optional[str] = None
    nome_fantasia: Optional[str] = None
    tipo: Optional[str] = None
    situacao_cadastral: Optional[str] = None
    data_inicio: Optional[str] = None
    uf: Optional[str] = None
    municipio: Optional[str] = None
    cnae_principal_codigo: Optional[str] = None
    cnae_principal_descricao: Optional[str] = None
    atual: bool = False

    model_config = {"from_attributes": True}


class EmpresaDetalhe(BaseModel):
    cnpj_basico: str
    cnpj_completo: Optional[str] = None
    cnpj_completo_formatado: Optional[str] = None
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    natureza_juridica_codigo: Optional[str] = None
    natureza_juridica_descricao: Optional[str] = None
    qualificacao_responsavel_codigo: Optional[str] = None
    qualificacao_responsavel_descricao: Optional[str] = None
    capital_social: Optional[str] = None
    porte: Optional[str] = None
    ente_federativo: Optional[str] = None
    situacao_cadastral: Optional[str] = None
    data_situacao: Optional[str] = None
    motivo_situacao: Optional[str] = None
    situacao_especial: Optional[str] = None
    data_situacao_especial: Optional[str] = None
    data_inicio: Optional[str] = None
    matriz_filial: Optional[str] = None
    tipo_logradouro: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cep: Optional[str] = None
    uf: Optional[str] = None
    municipio_codigo: Optional[str] = None
    municipio_descricao: Optional[str] = None
    ddd1: Optional[str] = None
    telefone1: Optional[str] = None
    ddd2: Optional[str] = None
    telefone2: Optional[str] = None
    email: Optional[str] = None
    cnae_principal_codigo: Optional[str] = None
    cnae_principal_descricao: Optional[str] = None
    cnae_secundarios: List[CnaeItem] = []
    opcao_simples: Optional[str] = None
    data_opcao_simples: Optional[str] = None
    data_exclusao_simples: Optional[str] = None
    opcao_mei: Optional[str] = None
    data_opcao_mei: Optional[str] = None
    data_exclusao_mei: Optional[str] = None
    socios_ativos: List[SocioCompleto] = []
    socios_inativos: List[SocioCompleto] = []
    filiais: List[FilialItem] = []
    dt_primeira_carga: Optional[str] = None
    dt_ultima_atualizacao: Optional[str] = None

    model_config = {"from_attributes": True}


class EmpresaListItem(BaseModel):
    cnpj_basico: str
    cnpj_completo: Optional[str] = None
    cnpj_completo_formatado: Optional[str] = None
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    situacao_cadastral: Optional[str] = None
    uf: Optional[str] = None
    municipio_descricao: Optional[str] = None

    model_config = {"from_attributes": True}


class SocioListItem(BaseModel):
    nome_socio: Optional[str] = None
    cpf_cnpj_socio: Optional[str] = None
    identificador: Optional[str] = None
    faixa_etaria: Optional[str] = None
    n_ativas: int = 0
    n_inaptas: int = 0
    n_ex: int = 0

    model_config = {"from_attributes": True}


class ListaResultados(BaseModel, Generic[T]):
    total: int
    resultados: List[T]
