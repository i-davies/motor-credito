from app.schemas import SolicitacaoCredito, ResultadoAnaliseCredito


def validar_dados_entrada(solicitacao: SolicitacaoCredito) -> None:
    """Aplica validacoes defensivas e limites de fronteira sobre os dados de entrada."""
    if solicitacao.idade < 18:
        raise ValueError("Idade minima permitida e 18 anos.")
    if solicitacao.idade > 75:
        raise ValueError("Idade maxima permitida e 75 anos.")

    if solicitacao.score_serasa < 0 or solicitacao.score_serasa > 1000:
        raise ValueError("Score Serasa deve estar entre 0 e 1000.")

    if solicitacao.renda_mensal <= 0:
        raise ValueError("Renda mensal deve ser maior que zero.")

    if solicitacao.valor_solicitado <= 0:
        raise ValueError("Valor solicitado deve ser maior que zero.")

    if solicitacao.quantidade_parcelas < 6:
        raise ValueError("Quantidade minima de parcelas e 6.")
    if solicitacao.quantidade_parcelas > 72:
        raise ValueError("Quantidade maxima de parcelas e 72.")

    if solicitacao.tempo_relacionamento_anos < 0:
        raise ValueError("Tempo de relacionamento nao pode ser negativo.")


def avaliar_solicitacao_credito(solicitacao: SolicitacaoCredito) -> ResultadoAnaliseCredito:
    """Executa o motor de regras de analise, score e concessao de credito."""
    validar_dados_entrada(solicitacao)

    # 1. Regra de Restricao Cadastral
    if solicitacao.possui_restricao_nome:
        return ResultadoAnaliseCredito(
            status="REPROVADO",
            categoria_risco="RESTRICAO",
            limite_maximo_aprovado=0.0,
            taxa_juros_mensal=0.0,
            valor_parcela=0.0,
            motivo="Restricao cadastral ativa no CPF."
        )

    # 2. Categorizacao por Faixa de Score
    if solicitacao.score_serasa < 300:
        return ResultadoAnaliseCredito(
            status="REPROVADO",
            categoria_risco="ALTO_RISCO_REPROVADO",
            limite_maximo_aprovado=0.0,
            taxa_juros_mensal=0.0,
            valor_parcela=0.0,
            motivo="Score de credito insuficiente para concessao."
        )
    elif solicitacao.score_serasa <= 599:
        categoria = "BRONZE"
        multiplicador = 2.0
        taxa_base = 0.085
    elif solicitacao.score_serasa <= 799:
        categoria = "PRATA"
        multiplicador = 4.0
        taxa_base = 0.045
    else:
        categoria = "OURO"
        multiplicador = 8.0
        taxa_base = 0.020

    limite_maximo = round(solicitacao.renda_mensal * multiplicador, 2)

    # 3. Calculo de Bonificacoes e Taxa Ajustada
    taxa_ajustada = taxa_base

    if solicitacao.tempo_relacionamento_anos >= 5 and solicitacao.score_serasa >= 600:
        taxa_ajustada -= 0.005

    if solicitacao.quantidade_parcelas <= 12:
        taxa_ajustada -= 0.002

    if taxa_ajustada < 0.014:
        taxa_ajustada = 0.014

    taxa_percentual = round(taxa_ajustada * 100, 2)

    # 4. Verificacao de Limite Maximo
    if solicitacao.valor_solicitado > limite_maximo:
        return ResultadoAnaliseCredito(
            status="REPROVADO",
            categoria_risco=categoria,
            limite_maximo_aprovado=limite_maximo,
            taxa_juros_mensal=taxa_percentual,
            valor_parcela=0.0,
            motivo=f"Valor solicitado excede o limite pre-aprovado de R$ {limite_maximo:.2f}."
        )

    # 5. Calculo da Parcela e Comprometimento de Renda
    total_com_juros = solicitacao.valor_solicitado * (1.0 + (taxa_ajustada * solicitacao.quantidade_parcelas))
    valor_parcela = round(total_com_juros / solicitacao.quantidade_parcelas, 2)
    comprometimento_maximo = round(solicitacao.renda_mensal * 0.30, 2)

    if valor_parcela > comprometimento_maximo:
        return ResultadoAnaliseCredito(
            status="REPROVADO",
            categoria_risco=categoria,
            limite_maximo_aprovado=limite_maximo,
            taxa_juros_mensal=taxa_percentual,
            valor_parcela=valor_parcela,
            motivo=f"Parcela de R$ {valor_parcela:.2f} excede 30% da renda mensal (R$ {comprometimento_maximo:.2f})."
        )

    return ResultadoAnaliseCredito(
        status="APROVADO",
        categoria_risco=categoria,
        limite_maximo_aprovado=limite_maximo,
        taxa_juros_mensal=taxa_percentual,
        valor_parcela=valor_parcela,
        motivo="Credito aprovado com sucesso."
    )