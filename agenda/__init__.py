"""Gerenciador de Agenda para Conferências Acadêmicas.

Seleciona, via algoritmo guloso (Activity Selection), o maior número de
palestras que podem ocorrer em uma única sala sem conflito de horário.
"""

from .modelos import Palestra
from .algoritmo import ResultadoAgenda, selecionar_palestras

__all__ = ["Palestra", "ResultadoAgenda", "selecionar_palestras"]
