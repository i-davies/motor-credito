import pytest
from fastapi.testclient import TestClient
from app.schemas import SolicitacaoCredito
from app.service import avaliar_solicitacao_credito


# ==============================================================================
# 1. TESTES DE CAIXA BRANCA: RAMIFICAÇÕES DE BONIFICAÇÃO E TAXA
# ==============================================================================

@pytest.mark.unit
@pytest.mark.whitebox
def test_ramificacao_desconto_fidelidade_e_prazo_curto():
    """Ramo: tempo >= 5 E score >= 600 E parcelas <= 12 (ambos descontos aplicados)."""
    # Score 700 (Prata: 4.5%), tempo=6 (desconto 0.5%), parcelas=10 (desconto 0.2%)
    # Taxa esperada: 4.5% - 0.5% - 0.2% = 3.8%
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


@pytest.mark.unit
@pytest.mark.whitebox
def test_ramificacao_tempo_insuficiente_para_fidelidade():
    """Ramo: tempo < 5 E score >= 600 (não ganha desconto de relacionamento)."""
    # Score 700 (Prata: 4.5%), tempo=2 (sem desconto), parcelas=24 (sem desconto prazo curto)
    # Taxa esperada: 4.5%
    solicitacao = SolicitacaoCredito(
        idade=30,
        renda_mensal=6000.0,
        score_serasa=700,
        valor_solicitado=2000.0,
        quantidade_parcelas=24,
        tempo_relacionamento_anos=2
    )
    resultado = avaliar_solicitacao_credito(solicitacao)
    assert resultado.status == "APROVADO"
    assert resultado.taxa_juros_mensal == 4.5


@pytest.mark.unit
@pytest.mark.whitebox
def test_ramificacao_score_insuficiente_para_fidelidade():
    """Ramo: tempo >= 5 E score < 600 (Bronze não ganha desconto de relacionamento)."""
    # Score 500 (Bronze: 8.5%), tempo=8, parcelas=24
    # Taxa esperada: 8.5%
    solicitacao = SolicitacaoCredito(
        idade=30,
        renda_mensal=6000.0,
        score_serasa=500,
        valor_solicitado=2000.0,
        quantidade_parcelas=24,
        tempo_relacionamento_anos=8
    )
    resultado = avaliar_solicitacao_credito(solicitacao)
    assert resultado.status == "APROVADO"
    assert resultado.taxa_juros_mensal == 8.5


@pytest.mark.unit
@pytest.mark.whitebox
def test_ramificacao_piso_taxa_minima():
    """Ramo: taxa ajustada cai abaixo do piso de 1.4% a.m. e é travada no piso."""
    # Score 900 (Ouro: 2.0%), tempo=10 (-0.5%), parcelas=6 (-0.2%) -> calculada: 1.3% -> piso: 1.4%
    solicitacao = SolicitacaoCredito(
        idade=30,
        renda_mensal=10000.0,
        score_serasa=900,
        valor_solicitado=1000.0,
        quantidade_parcelas=6,
        tempo_relacionamento_anos=10
    )
    resultado = avaliar_solicitacao_credito(solicitacao)
    assert resultado.status == "APROVADO"
    assert resultado.taxa_juros_mensal == 1.4


# ==============================================================================
# 2. TESTES DE CAIXA BRANCA: DECISÕES DE LIMITE E COMPROMETIMENTO
# ==============================================================================

@pytest.mark.unit
@pytest.mark.whitebox
def test_ramificacao_valor_solicitado_excede_limite_maximo():
    """Ramo: valor_solicitado > limite_maximo."""
    # Bronze: multiplicador 2.0 -> limite = R$ 4.000,00. Solicitado = R$ 5.000,00
    solicitacao = SolicitacaoCredito(
        idade=28,
        renda_mensal=2000.0,
        score_serasa=450,
        valor_solicitado=5000.0,
        quantidade_parcelas=12
    )
    resultado = avaliar_solicitacao_credito(solicitacao)
    assert resultado.status == "REPROVADO"
    assert resultado.limite_maximo_aprovado == 4000.0
    assert "excede o limite pre-aprovado" in resultado.motivo


@pytest.mark.unit
@pytest.mark.whitebox
def test_ramificacao_parcela_excede_comprometimento_renda():
    """Ramo: parcela > 30% da renda mensal."""
    solicitacao = SolicitacaoCredito(
        idade=28,
        renda_mensal=2000.0,
        score_serasa=450,
        valor_solicitado=3900.0,
        quantidade_parcelas=6
    )
    resultado = avaliar_solicitacao_credito(solicitacao)
    assert resultado.status == "REPROVADO"
    assert "excede 30% da renda mensal" in resultado.motivo


# ==============================================================================
# 3. TESTES DE INTEGRAÇÃO HTTP (FASTAPI)
# ==============================================================================

@pytest.mark.integration
def test_endpoint_health(client: TestClient):
    """Valida o endpoint de health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.integration
def test_endpoint_avaliar_credito_sucesso(client: TestClient):
    """Valida requisicao HTTP POST com payload aprovado."""
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


@pytest.mark.integration
def test_endpoint_avaliar_credito_validacao_invalida(client: TestClient):
    """Valida requisicao HTTP POST com idade menor que 18 (lanca 422)."""
    payload = {
        "idade": 16,
        "renda_mensal": 5000.0,
        "score_serasa": 850,
        "valor_solicitado": 10000.0,
        "quantidade_parcelas": 24
    }
    response = client.post("/credito/avaliar", json=payload)
    assert response.status_code == 422
    assert "Idade minima permitida e 18 anos." in response.json()["detail"]