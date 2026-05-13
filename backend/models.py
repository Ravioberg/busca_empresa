from sqlalchemy import Column, String, Integer, PrimaryKeyConstraint, UniqueConstraint
from database import Base


class CheckpointCarga(Base):
    __tablename__ = "tb_checkpoint_carga"
    mes           = Column(String(7),  nullable=False)
    tabela        = Column(String(30), nullable=False)
    qtd_inseridos = Column(Integer, default=0)
    __table_args__ = (PrimaryKeyConstraint("mes", "tabela"),)


class ProcessamentoMensal(Base):
    __tablename__ = "tb_processamento_mensal"
    id                              = Column(Integer, primary_key=True, autoincrement=True)
    dt_referencia                   = Column(String(7))   # YYYY-MM
    dt_processado                   = Column(String(19))  # YYYY-MM-DD HH:MM:SS
    qtd_inseridos_empresa           = Column(Integer, default=0)
    qtd_atualizados_empresa         = Column(Integer, default=0)
    qtd_inseridos_estabelecimento   = Column(Integer, default=0)
    qtd_atualizados_estabelecimento = Column(Integer, default=0)
    qtd_inseridos_socios            = Column(Integer, default=0)
    qtd_atualizados_socios          = Column(Integer, default=0)
    status                          = Column(String(20))  # CONCLUIDO | ERRO


class Empresa(Base):
    __tablename__ = "empresa"
    cd_cnpjbasico             = Column(String(8),  primary_key=True)
    nm_razaosocial            = Column(String(150))
    cd_naturezajuridica       = Column(String(4))
    cd_qualificacaoresponsavel = Column(String(2))
    vl_capitalsocial          = Column(String(20))
    cd_porteempresa           = Column(String(2))
    nm_entefederativo         = Column(String(50))
    dt_primeiracarga          = Column(String(7))
    dt_ultimaatualizacao      = Column(String(7))


class Estabelecimento(Base):
    __tablename__ = "estabelecimento"
    cd_cnpjbasico              = Column(String(8),   nullable=False)
    cd_cnpjordem               = Column(String(4),   nullable=False)
    cd_cnpjdv                  = Column(String(2))
    cd_identificadormatrizfilial = Column(String(1))
    nm_nomefantasia            = Column(String(75))
    cd_situacaocadastral       = Column(String(2))
    dt_datasituacaocadastral   = Column(String(8))
    cd_motivosituacaocadastral = Column(String(2))
    nm_cidadeexterior          = Column(String(55))
    cd_pais                    = Column(String(3))
    dt_datainicioatividade     = Column(String(8))
    cd_cnaefiscalprincipal     = Column(String(7))
    ds_cnaefiscalsecundaria    = Column(String(500))
    nm_tipologradouro          = Column(String(20))
    nm_logradouro              = Column(String(60))
    nm_numero                  = Column(String(6))
    nm_complemento             = Column(String(156))
    nm_bairro                  = Column(String(50))
    cd_cep                     = Column(String(8))
    sg_uf                      = Column(String(2))
    cd_municipio               = Column(String(4))
    cd_ddd1                    = Column(String(2))
    nr_telefone1               = Column(String(8))
    cd_ddd2                    = Column(String(2))
    nr_telefone2               = Column(String(8))
    cd_dddfax                  = Column(String(2))
    nr_fax                     = Column(String(8))
    nm_email                   = Column(String(115))
    nm_situacaoespecial        = Column(String(23))
    dt_datasituacaoespecial    = Column(String(8))
    dt_ultimaatualizacao       = Column(String(7))
    __table_args__ = (PrimaryKeyConstraint("cd_cnpjbasico", "cd_cnpjordem"),)


class Socio(Base):
    __tablename__ = "socio"
    id                                = Column(Integer, primary_key=True, autoincrement=True)
    cd_cnpjbasico                     = Column(String(8))
    cd_identificadorsocio             = Column(String(1))
    nm_nomesociorazaosocial           = Column(String(150))
    cd_cpfcnpjsocio                   = Column(String(14))
    cd_qualificacaosocio              = Column(String(2))
    dt_dataentradasociedade           = Column(String(8))
    cd_pais                           = Column(String(3))
    cd_cpfrepresentantelegal          = Column(String(11))
    nm_nomerepresentante              = Column(String(60))
    cd_qualificacaorepresentantelegal = Column(String(2))
    cd_faixaetaria                    = Column(String(1))
    dt_ultimaatualizacao              = Column(String(7))
    __table_args__ = (UniqueConstraint("cd_cnpjbasico", "cd_cpfcnpjsocio", "cd_qualificacaosocio"),)


class Simples(Base):
    __tablename__ = "simples"
    cd_cnpjbasico         = Column(String(8), primary_key=True)
    fl_opcaosimples       = Column(String(1))
    dt_dataopcaosimples   = Column(String(8))
    dt_dataexclusaosimples = Column(String(8))
    fl_opcaomei           = Column(String(1))
    dt_dataopcaomei       = Column(String(8))
    dt_dataexclusaomei    = Column(String(8))


class Cnae(Base):
    __tablename__ = "cnae"
    cd_cnae = Column(String(7), primary_key=True)
    ds_cnae = Column(String(200))


class Municipio(Base):
    __tablename__ = "municipio"
    cd_municipio = Column(String(4), primary_key=True)
    nm_municipio = Column(String(60))


class Natureza(Base):
    __tablename__ = "natureza"
    cd_naturezajuridica = Column(String(4), primary_key=True)
    ds_naturezajuridica = Column(String(150))


class Qualificacao(Base):
    __tablename__ = "qualificacao"
    cd_qualificacao = Column(String(2), primary_key=True)
    ds_qualificacao = Column(String(100))


class Motivo(Base):
    __tablename__ = "motivo"
    cd_motivosituacaocadastral = Column(String(2), primary_key=True)
    ds_motivosituacaocadastral = Column(String(100))


class Pais(Base):
    __tablename__ = "pais"
    cd_pais = Column(String(3), primary_key=True)
    nm_pais = Column(String(70))
