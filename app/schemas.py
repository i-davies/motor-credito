from pydantic import BaseModel, Field
from typing import Literal


class SolicitacaoCredito(BaseModel):
    idade: int = Field(..., description="Idade do solicitante em anos")
    renda_mensal: float = Field(..., description="Renda liquida mensal comprovada")
    score_serasa: int = Field(..., description="Pontuacao de credito de 0 a 1000")
    valor_solicitado: float = Field(..., description="Valor total do emprestimo solicitado")
    quantidade_parcelas: int = Field(..., description="Quantidade de parcelas mensais")
    possui_restricao_nome: bool = Field(default=False, description="Indica se ha restricao ativa no CPF")
    tempo_relacionamento_anos: int = Field(default=0, description="Tempo de relacionamento com o banco em anos")


class ResultadoAnaliseCredito(BaseModel):
    status: Literal["APROVADO", "REPROVADO"]
    categoria_risco: str
    limite_maximo_aprovado: float
    taxa_juros_mensal: float
    valor_parcela: float
    motivo: str