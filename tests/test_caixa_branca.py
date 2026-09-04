import pytest
from fastapi.testclient import TestClient
from app.schemas import SolicitacaoCredito
from app.service import avaliar_solicitacao_credito

# 1. Teste caixa branca: Ramificações de Bonificação e Taxa

@pytest.mark.unit
@pytest.mark.whitebox
def test_ramificacao_desconto_fidelidade_e_prazo_curto():
    solicitacao = SolicitacaoCredito(
        idade=30,
        renda_mensal=6000.0,
        score_serasa=700,
        valor_solicitado=2000.0,
        quantidade_parcelas=10,
        tempo_relacionamento_anos=6
    )
    resultado = avaliar_solicitacao_credito(solicitacao)
    assert resultado.status == "APROVADO"
    assert resultado.taxa_juros_mensal == 3.8

# 3. Testes de Integração HTTP (FASTAPI)
@pytest.mark.integration
def test_endpoint_health(client: TestClient):
    """Valida o endpoint de health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.integration
def test_endpoint_avaliar_credito_sucesso(client: TestClient):
    """ Valida requisição HTTP POST com payload aprovado."""
    payload = {
        "idade": 30,
        "renda_mensal": 5000.0,
        "score_serasa": 850,
        "valor_solicitado": 10000.0,
        "quantidade_parcelas": 24,
        "possui_restricao_nome": False,
        "tempo_relacionamento_anos": 5
    }
    response = client.post("/credito/avaliar", json=payload)
    assert response.status_code == 200
    dados = response.json()
    assert dados["status"] == "APROVADO"
    assert dados["categoria_risco"] == "OURO"