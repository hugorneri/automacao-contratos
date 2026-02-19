"""
Módulo de extração de dados das fichas de empregado (PDF).
Usa pdfplumber para extrair texto e regex para capturar os campos.
"""

import re
import pdfplumber
from typing import Optional

from src.utils import salario_extenso, formatar_data_local, limpar_texto


def extrair_dados_ficha(caminho_pdf: str) -> dict:
    """
    Extrai todos os campos necessários de uma ficha de empregado em PDF.
    Retorna um dicionário com as chaves sendo os placeholders (sem {{}}).
    """
    with pdfplumber.open(caminho_pdf) as pdf:
        texto_paginas = []
        palavras_paginas = []
        for page in pdf.pages:
            texto = page.extract_text(x_tolerance=2, y_tolerance=2)
            if texto:
                texto_paginas.append(texto)
            palavras = page.extract_words(x_tolerance=2, y_tolerance=2)
            palavras_paginas.append(palavras)
    
    texto_completo = "\n".join(texto_paginas)
    linhas = texto_completo.split("\n")
    
    dados = {}
    
    # --- Empregador (Empresa) ---
    empresa_raw = _extrair_campo_linha(linhas, r"^Empregador\b", offset_linha=1)
    # Remover CNPJ que pode estar junto
    cnpj = _extrair_regex(texto_completo, r"(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})")
    if cnpj and empresa_raw:
        empresa_raw = empresa_raw.replace(cnpj, "").strip()
    dados["EMPRESA"] = empresa_raw
    
    # --- CNPJ da empresa ---
    dados["EMPRESA_CNPJ"] = cnpj
    
    # --- Endereço da empresa ---
    dados["EMPRESA_ENDERECO"] = _extrair_campo_entre_labels(linhas, "Endereço", "Empregado")
    
    # --- Nome do empregado ---
    dados["NOME"] = _extrair_campo_linha(linhas, r"^Empregado\b", offset_linha=1)
    
    # --- Residência (endereço do empregado) ---
    dados["ENDERECO"] = _extrair_campo_entre_labels(linhas, "Residência", "Data de nascimento")
    
    # --- Data de nascimento, Local de nascimento, Nacionalidade, Estado civil ---
    # Estes campos ficam em uma linha de headers com valores tabulares abaixo.
    # Tentamos extrair usando posição das palavras no PDF ou regex no texto.
    dados["DATA_NASCIMENTO"] = _extrair_data_nascimento(linhas, palavras_paginas)
    dados["LOCAL_NASCIMENTO"] = _extrair_local_nascimento(linhas, palavras_paginas)
    dados["PAIS_NACIONALIDADE"] = _extrair_nacionalidade(linhas, palavras_paginas)
    dados["ESTADO_CIVIL"] = _extrair_estado_civil(linhas, palavras_paginas)
    
    # --- RG (Cédula de Identidade) ---
    dados["RG"] = _extrair_rg(linhas)
    
    # --- CTPS ---
    dados["CTPS"] = _extrair_ctps(linhas)
    
    # --- CTPS Série ---
    dados["CTPS_SERIE"] = _extrair_ctps_serie(linhas)
    
    # --- CPF ---
    dados["CPF"] = _extrair_regex(texto_completo, r"(\d{3}\.\d{3}\.\d{3}-\d{2})")
    
    # --- Função ---
    dados["FUNCAO"] = _extrair_funcao(linhas)
    
    # --- Salário ---
    dados["SALARIO"] = _extrair_salario(linhas)
    
    # --- Salário por extenso ---
    if dados["SALARIO"]:
        dados["SALARIO_EXTENSO"] = salario_extenso(dados["SALARIO"])
    else:
        dados["SALARIO_EXTENSO"] = ""
    
    # --- Período de experiência (dias) ---
    dados["PERIODO_EXPERIENCIA"] = _extrair_periodo_experiencia(linhas)
    
    # --- Dias de prorrogação ---
    dados["DIAS_PRORROGACAO"] = _extrair_dias_prorrogacao(linhas)
    
    # --- Data de admissão e local de assinatura ---
    data_admissao = _extrair_data_admissao(linhas)
    dados["DATA_ADMISSAO"] = data_admissao if data_admissao else ""
    if data_admissao:
        dados["DATA_LOCAL_ASSINATURA"] = formatar_data_local(data_admissao)
    else:
        dados["DATA_LOCAL_ASSINATURA"] = ""
    
    # --- Cidade (extraída do endereço da empresa) ---
    dados["CIDADE"] = _extrair_cidade(dados.get("EMPRESA_ENDERECO", ""))
    
    # Limpar todos os valores
    for chave in dados:
        if dados[chave]:
            dados[chave] = limpar_texto(dados[chave])
        else:
            dados[chave] = ""
    
    return dados


def _extrair_campo_linha(linhas: list, pattern: str, offset_linha: int = 1) -> str:
    """Encontra uma linha que corresponde ao pattern e retorna a linha com offset."""
    for i, linha in enumerate(linhas):
        if re.search(pattern, linha.strip(), re.IGNORECASE):
            idx = i + offset_linha
            if 0 <= idx < len(linhas):
                valor = linhas[idx].strip()
                return valor
    return ""


def _extrair_campo_entre_labels(linhas: list, label_inicio: str, label_fim: str) -> str:
    """Extrai texto entre duas linhas que contêm os labels especificados."""
    inicio = None
    fim = None
    for i, linha in enumerate(linhas):
        if label_inicio in linha and inicio is None:
            inicio = i + 1
        if label_fim in linha and inicio is not None:
            fim = i
            break
    
    if inicio is not None and fim is not None and inicio < fim:
        resultado = " ".join(linhas[inicio:fim]).strip()
        return resultado
    elif inicio is not None:
        if inicio < len(linhas):
            return linhas[inicio].strip()
    return ""


def _extrair_regex(texto: str, pattern: str) -> str:
    """Extrai o primeiro match de um regex no texto."""
    match = re.search(pattern, texto)
    return match.group(1) if match else ""


# ──────────────────────────────────────────────
# Campos tabulares: Data nascimento, Local, Nacionalidade, Estado civil
# Estes ficam na mesma linha de header e os valores podem estar
# logo abaixo em posições tabulares no PDF.
# Fallback: procuramos por padrões no texto extraído e usamos
# as palavras posicionais do pdfplumber como backup.
# ──────────────────────────────────────────────

def _encontrar_palavras_na_regiao(palavras_paginas: list, label: str, 
                                    y_offset: float = 15, 
                                    x_range: tuple = None) -> list:
    """
    Encontra palavras em uma região abaixo de um label no PDF.
    Retorna as palavras encontradas na região.
    """
    resultados = []
    for palavras in palavras_paginas:
        # Encontrar o label
        label_words = label.split()
        for i, w in enumerate(palavras):
            if w['text'] == label_words[0]:
                # Verificar se as outras palavras do label estão adjacentes
                match = True
                for j, lw in enumerate(label_words[1:], 1):
                    if i + j < len(palavras) and palavras[i + j]['text'] == lw:
                        continue
                    else:
                        match = False
                        break
                
                if match:
                    label_top = w['top']
                    label_x0 = w['x0']
                    # Buscar palavras logo abaixo do label
                    for pw in palavras:
                        if (label_top + 5 < pw['top'] < label_top + y_offset * 2 and
                            abs(pw['x0'] - label_x0) < 100):
                            resultados.append(pw['text'])
    return resultados


def _extrair_data_nascimento(linhas: list, palavras_paginas: list) -> str:
    """Extrai a data de nascimento."""
    # Primeiro, tentar encontrar a data na linha depois de "Data de nascimento"
    for i, linha in enumerate(linhas):
        if "Data de nascimento" in linha:
            # Verificar se há uma data na mesma linha (após o label)
            # O label completo é "Data de nascimento Local do nascimento..."
            # Procurar data nesta mesma linha que NÃO seja parte de outro campo
            match = re.search(r"Data de nascimento\s+.*?(\d{2}/\d{2}/\d{4})", linha)
            if match:
                return match.group(1)
            
            # Procurar nas próximas linhas (antes da seção FILIAÇÃO)
            for j in range(i + 1, min(i + 3, len(linhas))):
                if "FILIA" in linhas[j]:
                    break
                match = re.search(r"(\d{2}/\d{2}/\d{4})", linhas[j])
                if match:
                    return match.group(1)
            break
    
    # Fallback: usar posição das palavras
    words_found = _encontrar_palavras_na_regiao(palavras_paginas, "Data", y_offset=20)
    for w in words_found:
        if re.match(r"\d{2}/\d{2}/\d{4}", w):
            return w
    
    return ""


def _extrair_local_nascimento(linhas: list, palavras_paginas: list) -> str:
    """Extrai o local de nascimento."""
    # Procurar na linha de header
    for i, linha in enumerate(linhas):
        if "Local do nascimento" in linha:
            # Procurar texto entre "Local do nascimento" e "País da nacionalidade" 
            # na mesma linha ou na linha seguinte
            for j in range(i + 1, min(i + 3, len(linhas))):
                if "FILIA" in linhas[j] or "Pai" == linhas[j].strip():
                    break
                texto = linhas[j].strip()
                # Se a linha tem uma cidade/localidade
                if texto and not re.search(r"^\d{2}/\d{2}/\d{4}", texto):
                    return texto
            break
    return ""


def _extrair_nacionalidade(linhas: list, palavras_paginas: list) -> str:
    """Extrai o país da nacionalidade."""
    # Buscar no texto completo por palavras-chave de nacionalidade
    texto_completo = "\n".join(linhas)
    
    # Verificar se tem alguma nacionalidade explícita no PDF
    nacionalidades = [
        ("brasileiro", "Brasileiro(a)"),
        ("brasileira", "Brasileiro(a)"),
        ("brasil", "Brasileiro(a)"),
        ("portugu", "Português(a)"),
        ("argentin", "Argentino(a)"),
        ("bolivian", "Boliviano(a)"),
        ("paraguai", "Paraguaio(a)"),
        ("venezuel", "Venezuelano(a)"),
        ("haitian", "Haitiano(a)"),
    ]
    
    for kw, valor in nacionalidades:
        if kw in texto_completo.lower():
            return valor
    
    # Default
    return "Brasileiro(a)"


def _extrair_estado_civil(linhas: list, palavras_paginas: list) -> str:
    """Extrai o estado civil."""
    # Procurar no texto por palavras de estado civil
    estados_civis = [
        "solteiro", "solteira", "casado", "casada",
        "divorciado", "divorciada", "viúvo", "viúva",
        "separado", "separada", "união estável",
        "desquitado", "desquitada"
    ]
    
    texto_completo = "\n".join(linhas).lower()
    
    for estado in estados_civis:
        if estado in texto_completo:
            return estado.title()
    
    # Tentar encontrar via palavras posicionais (abaixo do label "Estado civil")
    words_found = _encontrar_palavras_na_regiao(palavras_paginas, "Estado", y_offset=20)
    for w in words_found:
        wl = w.lower()
        for estado in estados_civis:
            if estado in wl:
                return estado.title()
    
    return ""


def _extrair_rg(linhas: list) -> str:
    """Extrai o número do RG (Cédula de Identidade)."""
    for i, linha in enumerate(linhas):
        if "dula de Identidade" in linha or "Cédula de Identidade" in linha or "Cedula de Identidade" in linha:
            if i + 1 < len(linhas):
                texto = linhas[i + 1].strip()
                match = re.search(r"^(\d[\d.]*\d)", texto)
                if match:
                    return match.group(1)
                parts = texto.split()
                if parts:
                    # Verificar se o primeiro item parece um RG
                    if re.match(r"^\d+$", parts[0]):
                        return parts[0]
                    # Pode ser "SSP" sem RG, verificar se está vazio
                    if parts[0] == "SSP":
                        return ""
    return ""


def _extrair_ctps(linhas: list) -> str:
    """Extrai o número da CTPS."""
    for i, linha in enumerate(linhas):
        if re.search(r"^CTPS\b", linha.strip()):
            if i + 1 < len(linhas):
                texto = linhas[i + 1].strip()
                parts = texto.split()
                if parts:
                    for p in parts:
                        if re.match(r"^\d+$", p) and len(p) >= 4:
                            return p
    return ""


def _extrair_ctps_serie(linhas: list) -> str:
    """Extrai a série da CTPS."""
    for i, linha in enumerate(linhas):
        if "Série" in linha and "CTPS" in linha:
            if i + 1 < len(linhas):
                texto = linhas[i + 1].strip()
                parts = texto.split()
                # A série é geralmente o segundo item numérico
                numeros = [p for p in parts if re.match(r"^\d{1,5}$", p)]
                if len(numeros) >= 2:
                    return numeros[1]  # Segundo número = série
    return ""


def _extrair_funcao(linhas: list) -> str:
    """Extrai a função do empregado."""
    for i, linha in enumerate(linhas):
        if "Função" in linha and "C.B.O" in linha:
            if i + 1 < len(linhas):
                texto = linhas[i + 1].strip()
                # Remover o CBO (número de 6 dígitos no final)
                texto = re.sub(r"\s*\d{6}\s*$", "", texto)
                
                # O formato pode ser "Cargo FUNÇÃO" ou "FUNÇÃO" 
                # Se tem "Cargo" no header, o formato exato depende do PDF
                # Pega-se a última parte significativa como a função principal
                # Se houver algo como "Auxiliar de Producao AUXILIAR DE PRODUÇÃO"
                # Tenta detectar duplicados
                parts = texto.strip()
                if parts:
                    # Verificar se há texto duplicado (versão com/sem acentos)
                    palavras = parts.split()
                    # Pegar a segunda metade se for duplicado
                    meio = len(palavras) // 2
                    if meio >= 2:
                        primeira_metade = " ".join(palavras[:meio]).lower()
                        segunda_metade = " ".join(palavras[meio:]).lower()
                        # Comparar sem acentos/caracteres especiais
                        p1_clean = re.sub(r'[^a-z0-9 ]', '', primeira_metade)
                        p2_clean = re.sub(r'[^a-z0-9 ]', '', segunda_metade)
                        if p1_clean == p2_clean or _similaridade(p1_clean, p2_clean) > 0.7:
                            return " ".join(palavras[meio:])
                    return parts
    return ""


def _similaridade(s1: str, s2: str) -> float:
    """Calcula similaridade simples entre duas strings."""
    if not s1 or not s2:
        return 0.0
    palavras1 = set(s1.split())
    palavras2 = set(s2.split())
    if not palavras1 or not palavras2:
        return 0.0
    intersecao = palavras1 & palavras2
    uniao = palavras1 | palavras2
    return len(intersecao) / len(uniao)


def _extrair_salario(linhas: list) -> str:
    """Extrai o salário."""
    for i, linha in enumerate(linhas):
        if "Salário" in linha and "Data de Admissão" in linha:
            if i + 1 < len(linhas):
                texto = linhas[i + 1].strip()
                match = re.search(r"R\$\s*([\d.,]+)", texto)
                if match:
                    return match.group(1)
    return ""


def _extrair_data_admissao(linhas: list) -> str:
    """Extrai a data de admissão."""
    for i, linha in enumerate(linhas):
        if "Data de Admissão" in linha:
            if i + 1 < len(linhas):
                texto = linhas[i + 1].strip()
                match = re.search(r"(\d{2}/\d{2}/\d{4})", texto)
                if match:
                    return match.group(1)
    return ""


def _extrair_periodo_experiencia(linhas: list) -> str:
    """Extrai o período de experiência (quantidade de dias)."""
    for i, linha in enumerate(linhas):
        if "Quantidade de dias" in linha and "Contrato de Experiência" in linha:
            if i + 1 < len(linhas):
                texto = linhas[i + 1].strip()
                datas = re.findall(r"\d{2}/\d{2}/\d{4}", texto)
                numeros = re.findall(r"\b(\d{1,3})\b", texto)
                for n in numeros:
                    is_date_part = False
                    for d in datas:
                        if n in d:
                            is_date_part = True
                            break
                    if not is_date_part and 1 <= int(n) <= 120:
                        return n
    return ""


def _extrair_dias_prorrogacao(linhas: list) -> str:
    """Extrai os dias de prorrogação."""
    for i, linha in enumerate(linhas):
        if "Dias de prorrogação" in linha:
            if i + 1 < len(linhas):
                texto = linhas[i + 1].strip()
                datas = re.findall(r"\d{2}/\d{2}/\d{4}", texto)
                numeros = re.findall(r"\b(\d{1,3})\b", texto)
                for n in numeros:
                    is_date_part = False
                    for d in datas:
                        if n in d:
                            is_date_part = True
                            break
                    if not is_date_part and 1 <= int(n) <= 120:
                        return n
    return ""


def _extrair_cidade(endereco: str) -> str:
    """Extrai a cidade do endereço da empresa."""
    if not endereco:
        return "Campinas"
    partes = endereco.split(",")
    for i, parte in enumerate(partes):
        parte = parte.strip()
        if re.match(r"^[A-Z]{2}$", parte) and i > 0:
            cidade = partes[i - 1].strip()
            if cidade:
                return cidade.title()
    return "Campinas"


def extrair_multiplos_pdfs(caminhos: list) -> list:
    """
    Extrai dados de múltiplos PDFs.
    Retorna lista de dicionários, cada um com os dados de um empregado.
    """
    resultados = []
    for caminho in caminhos:
        try:
            dados = extrair_dados_ficha(caminho)
            dados["_arquivo"] = caminho
            resultados.append(dados)
        except Exception as e:
            resultados.append({
                "_arquivo": caminho,
                "_erro": str(e)
            })
    return resultados
