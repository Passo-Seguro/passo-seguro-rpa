from src.triagem.validacao import (
    validar_imagem,
    validar_coordenadas_sp,
    mascarar_lgpd,
    sanitizar_relato_lgpd
)


def test_validar_imagem_sucesso(imagem_valida_base64):
    valida, motivo = validar_imagem(imagem_valida_base64)
    assert valida is True
    assert "válida" in motivo.lower()


def test_validar_imagem_corrompida(imagem_invalida_base64):
    valida, motivo = validar_imagem(imagem_invalida_base64)
    assert valida is False
    assert "corrompida" in motivo.lower() or "inválido" in motivo.lower()


def test_validar_imagem_vazia():
    valida, motivo = validar_imagem("")
    assert valida is False
    assert "vazia" in motivo.lower() or "não informada" in motivo.lower()


def test_validar_coordenadas_dentro_sp():
    # Praça da Sé, SP
    valida, motivo = validar_coordenadas_sp(-23.5505, -46.6333)
    assert valida is True


def test_validar_coordenadas_fora_sp():
    # Santos / Litoral ou Rio de Janeiro
    valida, motivo = validar_coordenadas_sp(-22.9068, -43.1729)
    assert valida is False
    assert "fora da bounding box" in motivo.lower()


def test_mascaramento_lgpd():
    texto = "Meu CPF é 123.456.789-00 e meu telefone é (11) 98765-4321, favor verificar."
    mascarado = mascarar_lgpd(texto)
    assert "123.456.789-00" not in mascarado
    assert "***.***.***-**" in mascarado
    assert "98765-4321" not in mascarado
    assert "(**) *****-****" in mascarado


def test_sanitizar_relato_lgpd(relato_valido_se):
    relato_seguro = sanitizar_relato_lgpd(relato_valido_se)
    assert "***.***.***-**" in relato_seguro["autor_cpf"]
    assert "(**) *****-****" in relato_seguro["autor_telefone"]
