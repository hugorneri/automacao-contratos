# 📄 PROJETO: AUTOMAÇÃO DE CONTRATOS

---

## 🎯 Objetivo

Desenvolver um sistema desktop em **Python** para automatizar o preenchimento de contratos com base nos dados extraídos das fichas de empregados em PDF.

O sistema deverá:

* Ler fichas de colaboradores em PDF
* Extrair automaticamente as informações relevantes
* Preencher 4 modelos de contratos automaticamente
* Gerar um relatório consolidado em Excel (.xlsx)
* Organizar os arquivos gerados de forma estruturada

---

## 🛠 Tecnologias Obrigatórias

* Python 3.10+
* CustomTkinter (Interface gráfica)
* pdfplumber (Extração de dados de PDF)
* pandas (Manipulação de dados)
* openpyxl (Geração de arquivo XLSX)
* pathlib (Manipulação de caminhos)
* logging (Registro de eventos e erros)

---

## 📂 Estrutura de Pastas do Projeto

```
/Projeto
│
├── main.py
├── ui/
│   └── interface.py
├── services/
│   ├── extractor.py
│   ├── contract_generator.py
│   └── report_generator.py
│
├── Modelos/
│   └── (4 contratos modelo em PDF)
│
├── Fichas para teste/
│   └── (fichas PDF para validação)
│
├── Contratos Gerados/
├── Relatorios/
└── logs/
```

---

## ⚙️ Requisitos Funcionais

### 1️⃣ Interface Gráfica

A aplicação deve conter:

* Campo de upload para selecionar uma ou múltiplas fichas em PDF
* Botão "Processar"
* Barra de progresso
* Área de log/status mostrando:

  * Arquivo sendo processado
  * Sucesso ou erro
  * Tempo de execução

---

### 2️⃣ Extração de Dados

O sistema deve extrair das fichas os seguintes campos (ajustáveis conforme layout real):

* Nome completo
* CPF
* RG
* Cargo
* Salário
* Data de admissão
* Endereço
* Estado civil

Requisitos:

* Implementar validação de campos obrigatórios
* Tratar erros caso algum campo não seja encontrado
* Padronizar formatos (ex: datas, CPF, valores monetários)

---

### 3️⃣ Preenchimento dos Contratos

Para cada colaborador:

* Gerar 4 contratos baseados nos modelos da pasta `/Modelos`
* Substituir placeholders (ex: {{NOME}}, {{CPF}}, {{SALARIO}})
* Salvar os contratos na pasta `/Contratos Gerados`

Estrutura sugerida:

```
/Contratos Gerados/
    /NOME_COLABORADOR/
        contrato_1.pdf
        contrato_2.pdf
        contrato_3.pdf
        contrato_4.pdf
```

---

### 4️⃣ Geração de Relatório

Gerar automaticamente um arquivo:

```
/Relatorios/relatorio_processamento.xlsx
```

O relatório deve conter:

| Nome | CPF | Cargo | Salário | Data Admissão | Status | Observação |
| ---- | --- | ----- | ------- | ------------- | ------ | ---------- |

* Uma linha por colaborador
* Status: "Sucesso" ou "Erro"
* Observação: descrição do erro, se houver

---

## 🔎 Mapeamento de Placeholders

Os contratos utilizam placeholders que devem ser substituídos com base na extração via regex das fichas dos colaboradores.

### 📌 Estrutura: `PLACEHOLDER >> CAMPO DA FICHA (Regex)`

| Placeholder               | Campo na Ficha        | Observação                                         |
| ------------------------- | --------------------- | -------------------------------------------------- |
| {{EMPRESA}}               | Empregador            |                                                    |
| {{EMPRESA_ENDERECO}}      | Endereço              | Referente ao empregador                            |
| {{EMPRESA_CNPJ}}          | CNPJ                  | Referente ao empregador                            |
| {{NOME}}                  | Empregado             |                                                    |
| {{PAIS_NACIONALIDADE}}    | País da nacionalidade |                                                    |
| {{ESTADO_CIVIL}}          | Estado civil          |                                                    |
| {{DATA_NASCIMENTO}}       | Data de nascimento    | Padronizar formato                                 |
| {{LOCAL_NASCIMENTO}}      | Local do nascimento   |                                                    |
| {{ENDERECO}}              | Residência            | Endereço do empregado                              |
| {{CTPS}}                  | CTPS                  | Número da carteira                                 |
| {{CTPS_SERIE}}            | Série                 | Série da CTPS                                      |
| {{CPF}}                   | CPF                   | Aplicar máscara padrão                             |
| {{RG}}                    | Cédula de identidade  |                                                    |
| {{PERIODO_EXPERIENCIA}}   | Quantidade de dias    | Converter para número inteiro                      |
| {{FUNCAO}}                | Função                |                                                    |
| {{SALARIO}}               | Salario               | Padronizar formato monetário                       |
| {{SALARIO_EXTENSO}}       | Método específico     | Gerado via função própria para salário por extenso |
| {{DATA_LOCAL_ASSINATURA}} | Campo específico      | Método para gerar "Cidade, data" automaticamente   |
| {{DIAS_PRORROGACAO}}      | Quantidade de dias    | Caso exista prorrogação                            |

---

### ⚙️ Requisitos Específicos de Implementação

* A extração deve ser feita utilizando expressões regulares (regex) baseadas no layout da ficha.
* Criar um dicionário estruturado no formato:

```python
{
    "{{PLACEHOLDER}}": "valor_extraido"
}
```

* Implementar funções auxiliares para:

  * Conversão de salário para extenso
  * Padronização de datas
  * Formatação de CPF
  * Tratamento de valores monetários
  * Geração automática de campo de assinatura (cidade + data atual)

---

## 🧠 Requisitos Técnicos

* Código modular
* Separação clara de responsabilidades (UI, extração, contratos, relatório)
* Uso de classes
* Tratamento robusto de exceções
* Logging em arquivo dentro da pasta `/logs`
* Código documentado

---

## 🚀 Fluxo de Execução

1. Usuário seleciona fichas
2. Sistema valida arquivos
3. Extrai dados
4. Salva dados em DataFrame
5. Gera contratos
6. Atualiza relatório
7. Exibe resultado final

---

## 🔒 Requisitos de Qualidade

* Código limpo e organizado
* Fácil manutenção para adicionar novos campos
* Fácil inclusão de novos modelos de contrato
* Performance otimizada para múltiplos PDFs
* Interface intuitiva

---

## 📈 Possível Evolução Futura

* Transformar em sistema SaaS
* Upload via navegador
* Banco de dados (PostgreSQL)
* Assinatura digital integrada
* Controle de versões de contrato
* Dashboard de acompanhamento

---

## 📝 Observações Finais

O sistema deve ser pensado para:

* Escalabilidade
* Manutenção simples
* Facilidade de uso por equipe administrativa

Priorizar organização, clareza de código e robustez no tratamento de erros.
