"""Leitura de propostas a partir de arquivos JSON ou CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .modelos import Palestra


def palestras_de_dicts(registros: list[dict]) -> list[Palestra]:
    palestras = []
    for i, r in enumerate(registros, start=1):
        try:
            palestras.append(
                Palestra.de_horarios(
                    titulo=str(r["titulo"]),
                    inicio=str(r["inicio"]),
                    fim=str(r["fim"]),
                    palestrante=str(r.get("palestrante", "") or ""),
                )
            )
        except KeyError as e:
            raise ValueError(f"Proposta #{i}: campo obrigatório ausente: {e.args[0]}") from None
        except ValueError as e:
            raise ValueError(f"Proposta #{i}: {e}") from None
    return palestras


def carregar_arquivo(caminho: str | Path) -> list[Palestra]:
    """Lê um .json (lista de objetos ou {"palestras": [...]}) ou um .csv."""
    caminho = Path(caminho)
    sufixo = caminho.suffix.lower()

    if sufixo == ".json":
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        if isinstance(dados, dict):
            dados = dados.get("palestras", [])
        if not isinstance(dados, list):
            raise ValueError("O JSON deve ser uma lista de palestras ou {\"palestras\": [...]}")
        return palestras_de_dicts(dados)

    if sufixo == ".csv":
        with caminho.open(encoding="utf-8", newline="") as f:
            return palestras_de_dicts(list(csv.DictReader(f)))

    raise ValueError(f"Formato não suportado: {sufixo or '(sem extensão)'} — use .json ou .csv")
