"""
Interface gráfica do sistema de automação de contratos.
Usa CustomTkinter para uma aparência moderna.
"""

import os
import sys
import threading
import webbrowser
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Dict, List
import shutil

from src.pdf_extractor import extrair_dados_ficha, extrair_multiplos_pdfs
from src.doc_filler import preencher_contrato, gerar_contratos, listar_templates


# ──────────────────────────────────────────────
# Configuração do tema
# ──────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Caminho base do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_MODELOS = os.path.join(BASE_DIR, "Modelos")


# ──────────────────────────────────────────────
# Campos exibidos na interface para edição
# ──────────────────────────────────────────────
CAMPOS_EDITAVEIS = [
    ("EMPRESA", "Empresa"),
    ("EMPRESA_CNPJ", "CNPJ"),
    ("EMPRESA_ENDERECO", "Endereço Empresa"),
    ("NOME", "Nome do Empregado"),
    ("CPF", "CPF"),
    ("RG", "RG"),
    ("CTPS", "CTPS"),
    ("CTPS_SERIE", "CTPS Série"),
    ("DATA_NASCIMENTO", "Data de Nascimento"),
    ("LOCAL_NASCIMENTO", "Local de Nascimento"),
    ("PAIS_NACIONALIDADE", "País/Nacionalidade"),
    ("ESTADO_CIVIL", "Estado Civil"),
    ("ENDERECO", "Endereço"),
    ("CIDADE", "Cidade"),
    ("FUNCAO", "Função"),
    ("SALARIO", "Salário"),
    ("SALARIO_EXTENSO", "Salário por Extenso"),
    ("PERIODO_EXPERIENCIA", "Período Experiência (dias)"),
    ("QUANTIDADE_DIAS", "Quantidade de Dias"),
    ("DATA_FINAL", "Data Final Experiência"),
    ("DIAS_PRORROGACAO", "Dias de Prorrogação"),
    ("FIM_PRORROGACAO", "Fim da Prorrogação"),
    ("DATA_ADMISSAO", "Data de Admissão"),
    ("DATA_LOCAL_ASSINATURA", "Data/Local Assinatura"),
]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Automação de Contratos")
        self.geometry("1200x750")
        self.minsize(1000, 600)
        
        # Estado da aplicação
        self.dados_empregados: List[Dict[str, str]] = []
        self.arquivos_pdfs: List[str] = []  # Lista de caminhos dos PDFs carregados
        self.indice_atual = -1
        self.campos_entries: Dict[str, ctk.CTkEntry] = {}
        self.template_vars: Dict[str, ctk.BooleanVar] = {}
        
        self._criar_layout()
    
    # ──────────────────────────────────────────
    # Layout principal
    # ──────────────────────────────────────────
    def _criar_layout(self):
        # Grid principal: 2 colunas (sidebar + conteúdo)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._criar_sidebar()
        self._criar_area_principal()
    
    # ──────────────────────────────────────────
    # Sidebar (painel esquerdo)
    # ──────────────────────────────────────────
    def _criar_sidebar(self):
        # Usar frame rolável para garantir que todos os botões
        # fiquem acessíveis em telas menores (layout mais "responsivo")
        sidebar = ctk.CTkScrollableFrame(self, width=280, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="ns")
        
        # Título
        titulo = ctk.CTkLabel(
            sidebar, text="📄 Automação\nde Contratos",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        titulo.pack(pady=(25, 5))
        
        subtitulo = ctk.CTkLabel(
            sidebar, text="Gerador automático de contratos",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitulo.pack(pady=(0, 15))
        
        # Botão de Manual (no topo para fácil acesso)
        btn_manual = ctk.CTkButton(
            sidebar, 
            text="📖  Manual de Instruções",
            command=self._abrir_manual,
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        btn_manual.pack(padx=20, pady=(0, 15), fill="x")
        
        # Separador
        ctk.CTkFrame(sidebar, height=2, fg_color="gray30").pack(fill="x", padx=20, pady=5)
        
        # ── Seção: Upload de PDFs ──
        ctk.CTkLabel(
            sidebar, text="1. FICHAS DE EMPREGADO",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#4A9EFF"
        ).pack(pady=(15, 5), padx=20, anchor="w")
        
        btn_selecionar = ctk.CTkButton(
            sidebar, text="📂  Selecionar PDFs",
            command=self._selecionar_pdfs,
            height=38,
            font=ctk.CTkFont(size=13)
        )
        btn_selecionar.pack(padx=20, pady=(5, 5), fill="x")
        
        # Lista de arquivos carregados
        self.frame_lista_pdfs = ctk.CTkScrollableFrame(
            sidebar, height=120,
            label_text="Fichas carregadas",
            label_font=ctk.CTkFont(size=11)
        )
        self.frame_lista_pdfs.pack(padx=20, pady=(5, 10), fill="x")
        
        self.label_status_pdfs = ctk.CTkLabel(
            sidebar, text="Nenhuma ficha selecionada",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.label_status_pdfs.pack(padx=20, anchor="w")
        
        # Separador
        ctk.CTkFrame(sidebar, height=2, fg_color="gray30").pack(fill="x", padx=20, pady=10)
        
        # ── Seção: Templates ──
        ctk.CTkLabel(
            sidebar, text="2. MODELOS DE CONTRATO",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#4A9EFF"
        ).pack(pady=(5, 5), padx=20, anchor="w")

        btn_adicionar_template = ctk.CTkButton(
            sidebar,
            text="➕  Adicionar modelo (.docx)",
            command=self._adicionar_template,
            height=32,
            font=ctk.CTkFont(size=12)
        )
        btn_adicionar_template.pack(padx=20, pady=(0, 5), fill="x")

        self.frame_templates = ctk.CTkFrame(sidebar, fg_color="transparent")
        self.frame_templates.pack(padx=20, fill="x")
        self._carregar_templates()

        btn_remover_templates = ctk.CTkButton(
            sidebar,
            text="🗑  Remover modelos selecionados",
            command=self._remover_templates,
            height=30,
            font=ctk.CTkFont(size=11),
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        btn_remover_templates.pack(padx=20, pady=(5, 5), fill="x")
        
        # Separador
        ctk.CTkFrame(sidebar, height=2, fg_color="gray30").pack(fill="x", padx=20, pady=10)
        
        # ── Seção: Gerar ──
        ctk.CTkLabel(
            sidebar, text="3. GERAR CONTRATOS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#4A9EFF"
        ).pack(pady=(5, 5), padx=20, anchor="w")
        
        self.btn_gerar = ctk.CTkButton(
            sidebar, text="⚡  Gerar Contratos",
            command=self._gerar_contratos,
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#28a745",
            hover_color="#218838"
        )
        self.btn_gerar.pack(padx=20, pady=(5, 10), fill="x")
        
        self.label_status_geracao = ctk.CTkLabel(
            sidebar, text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=240
        )
        self.label_status_geracao.pack(padx=20, anchor="w")

        # Spacer para empurrar o rodapé para baixo
        spacer = ctk.CTkFrame(sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)
        
        # Rodapé
        ctk.CTkLabel(
            sidebar, text="v1.0 • T.I Automações",
            font=ctk.CTkFont(size=10),
            text_color="gray40"
        ).pack(pady=(0, 10))
    
    # ──────────────────────────────────────────
    # Área principal (painel central/direito)
    # ──────────────────────────────────────────
    def _criar_area_principal(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # ── Header: navegação entre empregados ──
        nav_frame = ctk.CTkFrame(main_frame, height=50)
        nav_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        nav_frame.grid_columnconfigure(1, weight=1)
        
        self.btn_anterior = ctk.CTkButton(
            nav_frame, text="◀  Anterior",
            command=self._empregado_anterior,
            width=120, state="disabled"
        )
        self.btn_anterior.grid(row=0, column=0, padx=10, pady=10)
        
        self.label_empregado = ctk.CTkLabel(
            nav_frame,
            text="Selecione fichas PDF para começar",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.label_empregado.grid(row=0, column=1, padx=10, pady=10)
        
        self.btn_proximo = ctk.CTkButton(
            nav_frame, text="Próximo  ▶",
            command=self._empregado_proximo,
            width=120, state="disabled"
        )
        self.btn_proximo.grid(row=0, column=2, padx=10, pady=10)
        
        # ── Formulário de dados ──
        self.form_frame = ctk.CTkScrollableFrame(
            main_frame,
            label_text="Dados do Empregado",
            label_font=ctk.CTkFont(size=14, weight="bold")
        )
        self.form_frame.grid(row=1, column=0, sticky="nsew")
        self.form_frame.grid_columnconfigure(1, weight=1)
        
        self._criar_campos_formulario()
    
    # ──────────────────────────────────────────
    # Criação dos campos do formulário
    # ──────────────────────────────────────────
    def _criar_campos_formulario(self):
        self.campos_entries = {}
        
        for i, (chave, label) in enumerate(CAMPOS_EDITAVEIS):
            lbl = ctk.CTkLabel(
                self.form_frame, text=f"{label}:",
                font=ctk.CTkFont(size=12),
                anchor="e",
                width=180
            )
            lbl.grid(row=i, column=0, padx=(10, 5), pady=4, sticky="e")
            
            entry = ctk.CTkEntry(
                self.form_frame,
                font=ctk.CTkFont(size=12),
                height=32
            )
            entry.grid(row=i, column=1, padx=(5, 10), pady=4, sticky="ew")
            
            self.campos_entries[chave] = entry
    
    # ──────────────────────────────────────────
    # Carregar templates
    # ──────────────────────────────────────────
    def _carregar_templates(self):
        # Limpar UI e estado anterior
        for widget in self.frame_templates.winfo_children():
            widget.destroy()
        self.template_vars.clear()

        templates = listar_templates(PASTA_MODELOS)
        
        if not templates:
            ctk.CTkLabel(
                self.frame_templates,
                text="Nenhum modelo encontrado\nem /Modelos",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).pack(pady=5)
            return
        
        for template in templates:
            nome = os.path.basename(template)
            # Remover extensão e número para exibição
            nome_exibicao = os.path.splitext(nome)[0]
            
            var = ctk.BooleanVar(value=True)  # Todos selecionados por padrão
            self.template_vars[template] = var
            
            cb = ctk.CTkCheckBox(
                self.frame_templates,
                text=nome_exibicao,
                variable=var,
                font=ctk.CTkFont(size=11),
                checkbox_width=20,
                checkbox_height=20
            )
            cb.pack(anchor="w", pady=2)
    
    # ──────────────────────────────────────────
    # Adicionar novo template (.docx)
    # ──────────────────────────────────────────
    def _adicionar_template(self):
        arquivo = filedialog.askopenfilename(
            title="Selecionar modelo de contrato (.docx)",
            filetypes=[("Arquivos Word", "*.docx")],
            initialdir=PASTA_MODELOS if os.path.exists(PASTA_MODELOS) else BASE_DIR,
        )

        if not arquivo:
            return

        if not arquivo.lower().endswith(".docx"):
            messagebox.showerror(
                "Arquivo inválido",
                "Selecione um arquivo .docx válido."
            )
            return

        nome_arquivo = os.path.basename(arquivo)
        destino = os.path.join(PASTA_MODELOS, nome_arquivo)

        try:
            os.makedirs(PASTA_MODELOS, exist_ok=True)

            if os.path.exists(destino):
                sobrescrever = messagebox.askyesno(
                    "Modelo já existe",
                    f"Já existe um modelo chamado:\n\n{nome_arquivo}\n\n"
                    "Deseja sobrescrever o arquivo existente?"
                )

                if not sobrescrever:
                    base, ext = os.path.splitext(nome_arquivo)
                    contador = 2
                    novo_destino = os.path.join(PASTA_MODELOS, f"{base}_{contador}{ext}")
                    while os.path.exists(novo_destino):
                        contador += 1
                        novo_destino = os.path.join(PASTA_MODELOS, f"{base}_{contador}{ext}")
                    destino = novo_destino

            shutil.copy2(arquivo, destino)
        except Exception as e:
            messagebox.showerror(
                "Erro ao adicionar modelo",
                "Não foi possível copiar o arquivo selecionado.\n\n"
                f"Detalhes do erro: {e}"
            )
            return

        messagebox.showinfo(
            "Modelo adicionado",
            f"O modelo foi adicionado com sucesso:\n\n{os.path.basename(destino)}"
        )

        self._carregar_templates()

    # ──────────────────────────────────────────
    # Remover templates selecionados
    # ──────────────────────────────────────────
    def _remover_templates(self):
        templates_marcados = [
            path for path, var in self.template_vars.items() if var.get()
        ]

        if not templates_marcados:
            messagebox.showinfo(
                "Remover modelos",
                "Nenhum modelo foi selecionado para remoção."
            )
            return

        nomes = "\n".join(os.path.basename(p) for p in templates_marcados)
        confirmar = messagebox.askyesno(
            "Confirmar remoção",
            "Os seguintes modelos serão removidos (arquivos serão apagados da pasta Modelos):\n\n"
            f"{nomes}\n\n"
            "Deseja continuar?"
        )

        if not confirmar:
            return

        removidos = 0
        erros = []

        for caminho in templates_marcados:
            try:
                if os.path.exists(caminho):
                    os.remove(caminho)
                    removidos += 1
            except Exception as e:
                erros.append(f"{os.path.basename(caminho)}: {e}")

        if removidos:
            msg = f"{removidos} modelo(s) removido(s) com sucesso."
            if erros:
                msg += f"\n\nAlguns modelos não puderam ser removidos:\n" + "\n".join(erros)
            messagebox.showinfo("Remover modelos", msg)
        else:
            messagebox.showwarning(
                "Remover modelos",
                "Nenhum modelo foi removido. Verifique se os arquivos ainda existem na pasta Modelos."
            )

        self._carregar_templates()

    # ──────────────────────────────────────────
    # Selecionar e processar PDFs
    # ──────────────────────────────────────────
    def _selecionar_pdfs(self):
        arquivos = filedialog.askopenfilenames(
            title="Selecionar Fichas de Empregado",
            filetypes=[("Arquivos PDF", "*.pdf")],
            initialdir=os.path.join(BASE_DIR, "Fichas para teste")
        )
        
        if not arquivos:
            return
        
        # Limpar lista anterior
        for widget in self.frame_lista_pdfs.winfo_children():
            widget.destroy()
        
        # Limpar dados anteriores se for uma nova seleção completa
        # (opcional: pode ser modificado para adicionar ao invés de substituir)
        self.dados_empregados = []
        self.arquivos_pdfs = []
        self.indice_atual = -1
        
        self.label_status_pdfs.configure(text="⏳ Extraindo dados...")
        self.update()
        
        # Processar em thread separada para não travar a UI
        thread = threading.Thread(target=self._processar_pdfs, args=(list(arquivos),))
        thread.start()
    
    def _processar_pdfs(self, arquivos: list):
        """Processa os PDFs em background."""
        self.dados_empregados = extrair_multiplos_pdfs(arquivos)
        # Manter referência aos arquivos para poder removê-los depois
        self.arquivos_pdfs = arquivos.copy()
        
        # Atualizar UI na thread principal
        self.after(0, lambda: self._atualizar_apos_extracao(arquivos))
    
    def _atualizar_apos_extracao(self, arquivos: list):
        """Atualiza a interface após extração."""
        self._atualizar_lista_fichas()
        
        # Mostrar primeiro empregado
        if self.dados_empregados:
            self.indice_atual = 0
            self._atualizar_formulario()
            self._atualizar_navegacao()
    
    def _atualizar_lista_fichas(self):
        """Atualiza a lista de fichas exibida na interface."""
        # Limpar lista anterior
        for widget in self.frame_lista_pdfs.winfo_children():
            widget.destroy()
        
        # Criar um frame para cada arquivo com botão de remoção
        for i, arquivo in enumerate(self.arquivos_pdfs):
            if i >= len(self.dados_empregados):
                continue
                
            nome = os.path.basename(arquivo)
            nome_curto = nome[:25] + "..." if len(nome) > 28 else nome
            
            # Verificar se teve erro
            has_error = "_erro" in self.dados_empregados[i] if i < len(self.dados_empregados) else False
            cor = "red" if has_error else None
            
            # Frame para cada item da lista
            frame_item = ctk.CTkFrame(self.frame_lista_pdfs, fg_color="transparent")
            frame_item.pack(fill="x", pady=2, padx=5)
            
            # Label com nome do arquivo
            lbl = ctk.CTkLabel(
                frame_item,
                text=f"{'❌' if has_error else '✅'} {nome_curto}",
                font=ctk.CTkFont(size=11),
                text_color=cor,
                anchor="w"
            )
            lbl.pack(side="left", fill="x", expand=True, padx=(0, 5))
            
            # Botão X para remover (usar função auxiliar para capturar índice corretamente)
            def criar_comando_remover(indice):
                return lambda: self._remover_ficha(indice)
            
            btn_remover = ctk.CTkButton(
                frame_item,
                text="✕",
                width=25,
                height=25,
                font=ctk.CTkFont(size=14, weight="bold"),
                fg_color="#dc3545",
                hover_color="#c82333",
                command=criar_comando_remover(i)
            )
            btn_remover.pack(side="right")
        
        # Atualizar status
        qtd = len(self.dados_empregados)
        erros = sum(1 for d in self.dados_empregados if "_erro" in d)
        self.label_status_pdfs.configure(
            text=f"✅ {qtd - erros} fichas extraídas" + (f" | ❌ {erros} erros" if erros else "")
        )
    
    def _remover_ficha(self, indice: int):
        """Remove uma ficha da lista."""
        if indice < 0 or indice >= len(self.dados_empregados):
            return
        
        # Remover da lista de dados
        self.dados_empregados.pop(indice)
        
        # Remover da lista de arquivos
        if indice < len(self.arquivos_pdfs):
            self.arquivos_pdfs.pop(indice)
        
        # Ajustar índice atual se necessário
        if self.indice_atual >= len(self.dados_empregados):
            self.indice_atual = len(self.dados_empregados) - 1
        
        # Se não há mais fichas, limpar formulário
        if not self.dados_empregados:
            self.indice_atual = -1
            for entry in self.campos_entries.values():
                entry.delete(0, "end")
            self.label_empregado.configure(text="Selecione fichas PDF para começar")
            self.label_status_pdfs.configure(text="Nenhuma ficha selecionada")
            self._atualizar_navegacao()
        else:
            # Ajustar índice se necessário
            if self.indice_atual < 0:
                self.indice_atual = 0
            elif self.indice_atual >= len(self.dados_empregados):
                self.indice_atual = len(self.dados_empregados) - 1
            
            # Atualizar formulário com o empregado atual
            if self.indice_atual >= 0:
                self._atualizar_formulario()
                self._atualizar_navegacao()
        
        # Atualizar lista visual
        self._atualizar_lista_fichas()
    
    # ──────────────────────────────────────────
    # Atualizar o formulário com dados do empregado
    # ──────────────────────────────────────────
    def _atualizar_formulario(self):
        if self.indice_atual < 0 or self.indice_atual >= len(self.dados_empregados):
            return
        
        dados = self.dados_empregados[self.indice_atual]
        
        if "_erro" in dados:
            self.label_empregado.configure(
                text=f"❌ Erro ao processar: {os.path.basename(dados.get('_arquivo', ''))}"
            )
            for entry in self.campos_entries.values():
                entry.delete(0, "end")
            return
        
        # Atualizar label do header
        nome = dados.get("NOME", "Empregado")
        self.label_empregado.configure(
            text=f"👤 {nome}  ({self.indice_atual + 1}/{len(self.dados_empregados)})"
        )
        
        # Preencher campos
        for chave, entry in self.campos_entries.items():
            entry.delete(0, "end")
            valor = dados.get(chave, "")
            entry.insert(0, valor)
    
    def _salvar_dados_formulario(self):
        """Salva os dados editados do formulário de volta no dicionário."""
        if self.indice_atual < 0 or self.indice_atual >= len(self.dados_empregados):
            return
        
        dados = self.dados_empregados[self.indice_atual]
        if "_erro" in dados:
            return
        
        for chave, entry in self.campos_entries.items():
            dados[chave] = entry.get()
    
    # ──────────────────────────────────────────
    # Navegação entre empregados
    # ──────────────────────────────────────────
    def _atualizar_navegacao(self):
        total = len(self.dados_empregados)
        self.btn_anterior.configure(state="normal" if self.indice_atual > 0 else "disabled")
        self.btn_proximo.configure(state="normal" if self.indice_atual < total - 1 else "disabled")
    
    def _empregado_anterior(self):
        self._salvar_dados_formulario()
        if self.indice_atual > 0:
            self.indice_atual -= 1
            self._atualizar_formulario()
            self._atualizar_navegacao()
    
    def _empregado_proximo(self):
        self._salvar_dados_formulario()
        if self.indice_atual < len(self.dados_empregados) - 1:
            self.indice_atual += 1
            self._atualizar_formulario()
            self._atualizar_navegacao()
    
    # ──────────────────────────────────────────
    # Gerar contratos
    # ──────────────────────────────────────────
    def _gerar_contratos(self):
        if not self.dados_empregados:
            messagebox.showwarning("Aviso", "Nenhuma ficha de empregado carregada.")
            return
        
        # Salvar dados atuais do formulário
        self._salvar_dados_formulario()
        
        # Verificar templates selecionados
        templates_selecionados = [
            path for path, var in self.template_vars.items() if var.get()
        ]
        
        if not templates_selecionados:
            messagebox.showwarning("Aviso", "Selecione pelo menos um modelo de contrato.")
            return
        
        # Selecionar pasta de destino
        pasta_saida = filedialog.askdirectory(
            title="Selecionar pasta de destino para os contratos"
        )
        
        if not pasta_saida:
            return
        
        self.btn_gerar.configure(state="disabled", text="⏳ Gerando...")
        self.label_status_geracao.configure(text="Processando...")
        self.update()
        
        # Gerar em thread separada
        thread = threading.Thread(
            target=self._processar_geracao,
            args=(templates_selecionados, pasta_saida)
        )
        thread.start()
    
    def _processar_geracao(self, templates: list, pasta_saida: str):
        """Gera os contratos em background."""
        total_gerados = 0
        total_erros = 0
        
        for dados in self.dados_empregados:
            if "_erro" in dados:
                total_erros += 1
                continue
            
            resultados = gerar_contratos(dados, templates, pasta_saida)
            for r in resultados:
                if r.startswith("ERRO:"):
                    total_erros += 1
                else:
                    total_gerados += 1
        
        # Atualizar UI na thread principal
        self.after(0, lambda: self._finalizar_geracao(total_gerados, total_erros, pasta_saida))
    
    def _finalizar_geracao(self, total_gerados: int, total_erros: int, pasta_saida: str):
        """Atualiza a interface após geração."""
        self.btn_gerar.configure(state="normal", text="⚡  Gerar Contratos")
        
        msg = f"✅ {total_gerados} contratos gerados"
        if total_erros:
            msg += f" | ❌ {total_erros} erros"
        
        self.label_status_geracao.configure(text=msg)
        
        messagebox.showinfo(
            "Contratos Gerados",
            f"{total_gerados} contratos foram gerados com sucesso!\n\n"
            f"Pasta: {pasta_saida}"
            + (f"\n\n{total_erros} erros encontrados." if total_erros else "")
        )
        
        # Abrir pasta de saída
        os.startfile(pasta_saida)
    
    # ──────────────────────────────────────────
    # Abrir manual de instruções
    # ──────────────────────────────────────────
    def _abrir_manual(self):
        """Abre o manual de instruções no navegador padrão."""
        caminho_manual = os.path.join(BASE_DIR, "manual.html")
        
        if os.path.exists(caminho_manual):
            # Abrir no navegador padrão
            caminho_absoluto = os.path.abspath(caminho_manual)
            webbrowser.open(f"file:///{caminho_absoluto.replace(os.sep, '/')}")
        else:
            messagebox.showerror(
                "Erro",
                f"Arquivo do manual não encontrado:\n{caminho_manual}\n\n"
                "Entre em contato com o suporte técnico."
            )


def iniciar_app():
    """Inicia a aplicação."""
    app = App()
    app.mainloop()
