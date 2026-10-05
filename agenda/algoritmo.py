"""Algoritmo guloso de seleção de atividades (Activity Selection Problem).

Estratégia: ordenar as palestras pelo horário de término e, percorrendo-as
nessa ordem, aceitar cada uma que comece depois (ou exatamente quando) a
última aceita terminou.

Por que funciona (escolha gulosa): a palestra que termina mais cedo deixa a
sala livre o quanto antes, então sempre existe uma solução ótima que a
contém. Trocando a primeira palestra de qualquer solução ótima por ela, a
solução continua válida e com o mesmo tamanho; o argumento se repete para o
subproblema restante.

Complexidade: O(n log n) pela ordenação + O(n) para a varredura.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .modelos import Palestra


@dataclass
class ResultadoAgenda:
    aceitas: list[Palestra]
    rejeitadas: list[Palestra]
    # Para cada palestra rejeitada, as aceitas que ocupam parte do seu horário.
    conflitos: dict[Palestra, list[Palestra]] = field(default_factory=dict)
    janela_inicio: int = 0
    janela_fim: int = 0

    @property
    def tempo_ocupado(self) -> int:
        """Minutos de sala ocupados pelas palestras aceitas."""
        return sum(p.duracao for p in self.aceitas)

    @property
    def tempo_janela(self) -> int:
        """Duração total da janela do evento, em minutos."""
        return max(0, self.janela_fim - self.janela_inicio)

    @property
    def tempo_ocioso(self) -> int:
        return self.tempo_janela - self.tempo_ocupado

    @property
    def taxa_ocupacao(self) -> float:
        """Fração (0..1) da janela do evento em que a sala está ocupada."""
        return self.tempo_ocupado / self.tempo_janela if self.tempo_janela else 0.0

    def para_dict(self) -> dict:
        return {
            "aceitas": [p.para_dict() for p in self.aceitas],
            "rejeitadas": [
                {**p.para_dict(), "conflita_com": [c.titulo for c in self.conflitos.get(p, [])]}
                for p in self.rejeitadas
            ],
            "resumo": {
                "total_propostas": len(self.aceitas) + len(self.rejeitadas),
                "total_aceitas": len(self.aceitas),
                "total_rejeitadas": len(self.rejeitadas),
                "tempo_ocupado_min": self.tempo_ocupado,
                "tempo_janela_min": self.tempo_janela,
                "tempo_ocioso_min": self.tempo_ocioso,
                "taxa_ocupacao": round(self.taxa_ocupacao, 4),
            },
        }


def selecionar_palestras(
    palestras: list[Palestra],
    janela_inicio: int | None = None,
    janela_fim: int | None = None,
) -> ResultadoAgenda:
    """Retorna a grade com o número máximo de palestras sem conflito.

    Se a janela do evento não for informada, ela vai do início mais cedo ao
    fim mais tarde entre as propostas. Palestras fora da janela são rejeitadas.
    """
    if janela_inicio is None:
        janela_inicio = min((p.inicio for p in palestras), default=0)
    if janela_fim is None:
        janela_fim = max((p.fim for p in palestras), default=0)

    # Desempate pelo início para que o resultado seja determinístico.
    ordenadas = sorted(palestras, key=lambda p: (p.fim, p.inicio, p.titulo))

    aceitas: list[Palestra] = []
    rejeitadas: list[Palestra] = []
    fim_ultima = janela_inicio

    for palestra in ordenadas:
        dentro_da_janela = palestra.inicio >= janela_inicio and palestra.fim <= janela_fim
        if dentro_da_janela and palestra.inicio >= fim_ultima:
            aceitas.append(palestra)
            fim_ultima = palestra.fim
        else:
            rejeitadas.append(palestra)

    conflitos = {r: [a for a in aceitas if a.conflita_com(r)] for r in rejeitadas}
    rejeitadas.sort(key=lambda p: (p.inicio, p.fim))

    return ResultadoAgenda(aceitas, rejeitadas, conflitos, janela_inicio, janela_fim)
