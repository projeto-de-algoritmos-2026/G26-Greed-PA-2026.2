"""Relatório formatado para o terminal."""

from __future__ import annotations

from .algoritmo import ResultadoAgenda
from .modelos import Palestra, minutos_para_horario

VERDE = "\033[32m"
VERMELHO = "\033[31m"
AMARELO = "\033[33m"
CIANO = "\033[36m"
NEGRITO = "\033[1m"
ESMAECIDO = "\033[2m"
RESET = "\033[0m"


class Estilo:
    def __init__(self, cores: bool) -> None:
        self.cores = cores

    def __call__(self, texto: str, *codigos: str) -> str:
        if not self.cores or not codigos:
            return texto
        return "".join(codigos) + texto + RESET


def formatar_duracao(minutos: int) -> str:
    h, m = divmod(minutos, 60)
    if h and m:
        return f"{h}h{m:02d}min"
    return f"{h}h" if h else f"{m}min"


def _cortar(texto: str, largura: int) -> str:
    return texto if len(texto) <= largura else texto[: largura - 1] + "…"


def _tabela(cabecalho: list[str], linhas: list[list[str]], estilo: Estilo, cor: str) -> str:
    larguras = [max(len(c), *(len(l[i]) for l in linhas)) for i, c in enumerate(cabecalho)]

    def borda(esq: str, meio: str, dir: str) -> str:
        return esq + meio.join("─" * (w + 2) for w in larguras) + dir

    def linha(celulas: list[str]) -> str:
        return "│" + "│".join(f" {c.ljust(w)} " for c, w in zip(celulas, larguras)) + "│"

    saida = [borda("┌", "┬", "┐"), estilo(linha(cabecalho), NEGRITO, cor), borda("├", "┼", "┤")]
    saida += [linha(l) for l in linhas]
    saida.append(borda("└", "┴", "┘"))
    return "\n".join(saida)


def _linha_do_tempo(resultado: ResultadoAgenda, estilo: Estilo, largura: int = 60) -> str:
    inicio, fim = resultado.janela_inicio, resultado.janela_fim
    total = fim - inicio
    if total <= 0:
        return ""

    def coluna(minuto: int) -> int:
        return round((minuto - inicio) / total * largura)

    barra = [" "] * largura
    for p in resultado.aceitas:
        a, b = coluna(p.inicio), max(coluna(p.fim), coluna(p.inicio) + 1)
        for i in range(a, min(b, largura)):
            barra[i] = "█"

    ocupado = "".join(estilo(c, VERDE) if c == "█" else estilo("·", ESMAECIDO) for c in barra)
    rotulo_ini, rotulo_fim = minutos_para_horario(inicio), minutos_para_horario(fim)
    regua = rotulo_ini + " " * (largura - len(rotulo_ini) - len(rotulo_fim)) + rotulo_fim
    return f"  Sala  │{ocupado}│\n         {regua}"


def renderizar(resultado: ResultadoAgenda, cores: bool = True) -> str:
    e = Estilo(cores)
    blocos: list[str] = []

    total = len(resultado.aceitas) + len(resultado.rejeitadas)
    titulo = " GRADE DE PALESTRAS — SALA ÚNICA "
    blocos.append(e("═" * 70, CIANO))
    blocos.append(e(titulo.center(70), NEGRITO, CIANO))
    blocos.append(e("═" * 70, CIANO))
    blocos.append(
        f"Janela do evento: {minutos_para_horario(resultado.janela_inicio)} – "
        f"{minutos_para_horario(resultado.janela_fim)}   ·   Propostas recebidas: {total}"
    )

    # Aceitas
    blocos.append("")
    blocos.append(e(f"✔ PALESTRAS ACEITAS ({len(resultado.aceitas)})", NEGRITO, VERDE))
    if resultado.aceitas:
        linhas = [
            [str(i), f"{p.inicio_str}–{p.fim_str}", formatar_duracao(p.duracao),
             _cortar(p.titulo, 38), _cortar(p.palestrante or "—", 22)]
            for i, p in enumerate(resultado.aceitas, start=1)
        ]
        blocos.append(_tabela(["#", "Horário", "Duração", "Título", "Palestrante"], linhas, e, VERDE))
    else:
        blocos.append("  (nenhuma)")

    # Rejeitadas
    blocos.append("")
    blocos.append(e(f"✘ PALESTRAS REJEITADAS ({len(resultado.rejeitadas)})", NEGRITO, VERMELHO))
    if resultado.rejeitadas:
        linhas = [
            [f"{p.inicio_str}–{p.fim_str}", _cortar(p.titulo, 34), _motivo(p, resultado)]
            for p in resultado.rejeitadas
        ]
        blocos.append(_tabela(["Horário", "Título", "Motivo"], linhas, e, VERMELHO))
    else:
        blocos.append("  (nenhuma)")

    # Linha do tempo e resumo
    blocos.append("")
    blocos.append(e("LINHA DO TEMPO DA SALA", NEGRITO, CIANO))
    blocos.append(_linha_do_tempo(resultado, e))

    blocos.append("")
    blocos.append(e("RESUMO DE APROVEITAMENTO", NEGRITO, CIANO))
    pct = resultado.taxa_ocupacao * 100
    cor_pct = VERDE if pct >= 75 else AMARELO if pct >= 50 else VERMELHO
    preenchido = round(resultado.taxa_ocupacao * 40)
    barra = e("█" * preenchido, cor_pct) + e("░" * (40 - preenchido), ESMAECIDO)
    blocos.append(f"  Tempo total aproveitado : {e(formatar_duracao(resultado.tempo_ocupado), NEGRITO)}")
    blocos.append(f"  Tempo ocioso da sala    : {formatar_duracao(resultado.tempo_ocioso)}")
    blocos.append(f"  Duração da janela       : {formatar_duracao(resultado.tempo_janela)}")
    blocos.append(f"  Ocupação                : {barra} {e(f'{pct:.1f}%', NEGRITO, cor_pct)}")
    blocos.append(e("═" * 70, CIANO))

    return "\n".join(blocos)


def _motivo(p: Palestra, resultado: ResultadoAgenda) -> str:
    conflitos = resultado.conflitos.get(p, [])
    if not conflitos:
        return "Fora da janela do evento"
    nomes = " + ".join(_cortar(c.titulo, 28) for c in conflitos)
    return _cortar(f"Conflita com: {nomes}", 72)
