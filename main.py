"""
Automação de Contratos - Sistema de Geração Automática
Ponto de entrada principal do sistema.

Uso: python main.py
"""

import sys
import os

# Garantir que o diretório do projeto está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import iniciar_app


if __name__ == "__main__":
    iniciar_app()
