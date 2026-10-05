"""Modelos de dados do sistema."""

from __future__ import annotations

from dataclasses import dataclass


def horario_para_minutos(horario: str) -> int:
    """Converte "HH:MM" em minutos desde 00:00."""
    try:
        horas, minutos = horario.strip().split(":")
        h, m = int(horas), int(minutos)
    except (ValueError, AttributeError):
        raise ValueError(f"Horário inválido: {horario!r} (use o formato HH:MM)")
    if not (0 <= h <= 24 and 0 <= m < 60) or (h == 24 and m != 0):
        raise ValueError(f"Horário fora do intervalo válido: {horario!r}")
    return h * 60 + m


def minutos_para_horario(minutos: int) -> str:
    """Converte minutos desde 00:00 em "HH:MM"."""
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


@dataclass(frozen=True)
class Palestra:
    """Uma proposta de palestra com intervalo [inicio, fim) em minutos."""

    titulo: str
    inicio: int
    fim: int
    palestrante: str = ""

    def __post_init__(self) -> None:
        if not self.titulo.strip():
            raise ValueError("A palestra precisa ter um título")
        if self.fim <= self.inicio:
            raise ValueError(
                f"Palestra {self.titulo!r}: o fim ({minutos_para_horario(self.fim)}) "
                f"deve ser depois do início ({minutos_para_horario(self.inicio)})"
            )

    @classmethod
    def de_horarios(cls, titulo: str, inicio: str, fim: str, palestrante: str = "") -> Palestra:
        return cls(titulo, horario_para_minutos(inicio), horario_para_minutos(fim), palestrante)

    @property
    def duracao(self) -> int:
        return self.fim - self.inicio

    @property
    def inicio_str(self) -> str:
        return minutos_para_horario(self.inicio)

    @property
    def fim_str(self) -> str:
        return minutos_para_horario(self.fim)

    def conflita_com(self, outra: Palestra) -> bool:
        """Intervalos semiabertos: terminar às 10:00 e começar às 10:00 não conflita."""
        return self.inicio < outra.fim and outra.inicio < self.fim

    def para_dict(self) -> dict:
        return {
            "titulo": self.titulo,
            "palestrante": self.palestrante,
            "inicio": self.inicio_str,
            "fim": self.fim_str,
            "duracao_min": self.duracao,
        }
