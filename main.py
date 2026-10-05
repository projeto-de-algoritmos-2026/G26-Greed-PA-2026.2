"""Ponto de entrada da linha de comando.

Exemplos:
  python main.py exemplos/palestras.json
  python main.py exemplos/palestras.csv --inicio 08:00 --fim 18:00
  python main.py exemplos/palestras.json --json
  python main.py --api --porta 8000
"""

from __future__ import annotations

import argparse
import json
import sys

from agenda.algoritmo import selecionar_palestras
from agenda.leitor import carregar_arquivo
from agenda.modelos import horario_para_minutos
from agenda.visualizacao import renderizar


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calcula a grade máxima de palestras sem conflito em uma única sala.",
    )
    parser.add_argument("arquivo", nargs="?", help="arquivo .json ou .csv com as propostas")
    parser.add_argument("--inicio", help="início da janela do evento (HH:MM)")
    parser.add_argument("--fim", help="fim da janela do evento (HH:MM)")
    parser.add_argument("--json", action="store_true", help="imprime o resultado em JSON")
    parser.add_argument("--sem-cor", action="store_true", help="desativa as cores ANSI")
    parser.add_argument("--api", action="store_true", help="inicia a API HTTP")
    parser.add_argument("--host", default="127.0.0.1", help="host da API (padrão: 127.0.0.1)")
    parser.add_argument("--porta", type=int, default=8000, help="porta da API (padrão: 8000)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = criar_parser()
    args = parser.parse_args(argv)

    if args.api:
        from agenda.api import servir
        servir(args.host, args.porta)
        return 0

    if not args.arquivo:
        parser.error("informe o arquivo de propostas ou use --api")

    try:
        palestras = carregar_arquivo(args.arquivo)
        inicio = horario_para_minutos(args.inicio) if args.inicio else None
        fim = horario_para_minutos(args.fim) if args.fim else None
    except FileNotFoundError:
        print(f"Erro: arquivo não encontrado: {args.arquivo}", file=sys.stderr)
        return 1
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1

    resultado = selecionar_palestras(palestras, inicio, fim)

    if args.json:
        print(json.dumps(resultado.para_dict(), ensure_ascii=False, indent=2))
    else:
        cores = not args.sem_cor and sys.stdout.isatty()
        print(renderizar(resultado, cores=cores))
    return 0


if __name__ == "__main__":
    sys.exit(main())
