from fastapi import FastAPI, HTTPException
from app.schemas import SolicitacaoCredito, ResultadoAnaliseCredito
from app.service import avaliar_solicitacao_credito

app = FastAPI(
    title="Motor de Crédito API",
    description="Api para análise automatizada de crétido.",
    version="1.0.0",
)

@app.get("/health")
def health_check():
    """ Endpoint de verificação de integridade da API. """
    return { "status": "healthy", "service": "motor-credito" }

@app.post("/credito/avaliar", response_model=ResultadoAnaliseCredito)
def endpoint_avaliar_credito(solicitacao: SolicitacaoCredito):
    """ Processa a solicitação de crédito aplicando regras de negócio e limites. """
    try:
        resultado = avaliar_solicitacao_credito(solicitacao)
        return resultado
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))