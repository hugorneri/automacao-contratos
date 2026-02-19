"""
Funções utilitárias para o sistema de automação de contratos.
"""

import re
from datetime import datetime


def salario_extenso(valor_str: str) -> str:
    """
    Converte um valor monetário em string (ex: '2.186,28') para texto por extenso.
    Retorna algo como: 'dois mil, cento e oitenta e seis reais e vinte e oito centavos'
    """
    # Limpar o valor
    valor_str = valor_str.replace("R$", "").replace(" ", "").strip()
    
    # Separar reais e centavos
    if "," in valor_str:
        partes = valor_str.split(",")
        reais_str = partes[0].replace(".", "")
        centavos_str = partes[1]
    else:
        reais_str = valor_str.replace(".", "")
        centavos_str = "00"
    
    reais = int(reais_str)
    centavos = int(centavos_str)
    
    texto_reais = _numero_extenso(reais)
    
    resultado = ""
    if reais == 1:
        resultado = f"{texto_reais} real"
    elif reais > 1:
        resultado = f"{texto_reais} reais"
    
    if centavos > 0:
        texto_centavos = _numero_extenso(centavos)
        if resultado:
            resultado += " e "
        if centavos == 1:
            resultado += f"{texto_centavos} centavo"
        else:
            resultado += f"{texto_centavos} centavos"
    
    return resultado


def _numero_extenso(n: int) -> str:
    """Converte um número inteiro para texto por extenso (até 999.999)."""
    if n == 0:
        return "zero"
    
    unidades = [
        "", "um", "dois", "três", "quatro", "cinco",
        "seis", "sete", "oito", "nove", "dez",
        "onze", "doze", "treze", "quatorze", "quinze",
        "dezesseis", "dezessete", "dezoito", "dezenove"
    ]
    
    dezenas = [
        "", "", "vinte", "trinta", "quarenta", "cinquenta",
        "sessenta", "setenta", "oitenta", "noventa"
    ]
    
    centenas = [
        "", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos",
        "seiscentos", "setecentos", "oitocentos", "novecentos"
    ]
    
    if n == 100:
        return "cem"
    
    partes = []
    
    if n >= 1000:
        milhares = n // 1000
        n = n % 1000
        if milhares == 1:
            partes.append("mil")
        else:
            partes.append(f"{_numero_extenso(milhares)} mil")
    
    if n >= 100:
        c = n // 100
        partes.append(centenas[c])
        n = n % 100
    
    if n >= 20:
        d = n // 10
        partes.append(dezenas[d])
        n = n % 10
    
    if 0 < n < 20:
        partes.append(unidades[n])
    
    # Juntar com "e"
    if len(partes) == 1:
        return partes[0]
    
    # Última parte sempre com "e"
    resultado = partes[0]
    for i in range(1, len(partes)):
        resultado += " e " + partes[i]
    
    return resultado


MESES = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
}


def formatar_data_local(data_str: str, cidade: str = "Campinas") -> str:
    """
    Converte data DD/MM/YYYY para formato por extenso.
    Ex: '23/01/2024' -> 'Campinas, 23 de janeiro de 2024'
    """
    try:
        partes = data_str.strip().split("/")
        dia = int(partes[0])
        mes = int(partes[1])
        ano = int(partes[2])
        nome_mes = MESES.get(mes, str(mes))
        return f"{cidade}, {dia} de {nome_mes} de {ano}"
    except (ValueError, IndexError):
        return f"{cidade}, {data_str}"


def limpar_texto(texto: str) -> str:
    """Remove espaços extras e quebras de linha desnecessárias."""
    if not texto:
        return ""
    return " ".join(texto.split()).strip()
