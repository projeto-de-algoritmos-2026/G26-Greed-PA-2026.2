"""API HTTP simples (somente biblioteca padrão).

Endpoints:
  GET  /               -> instruções de uso
  POST /agenda         -> recebe {"palestras": [...], "janela": {"inicio": "08:00", "fim": "18:00"}}
                          e devolve as palestras aceitas, rejeitadas e o resumo.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .algoritmo import selecionar_palestras
from .leitor import palestras_de_dicts
from .modelos import horario_para_minutos

INSTRUCOES = {
    "servico": "Gerenciador de Agenda para Conferências Acadêmicas",
    "uso": "POST /agenda com JSON",
    "exemplo": {
        "palestras": [
            {"titulo": "Abertura", "inicio": "08:00", "fim": "09:00", "palestrante": "Comissão"},
            {"titulo": "Grafos", "inicio": "08:30", "fim": "10:00"},
        ],
        "janela": {"inicio": "08:00", "fim": "18:00"},
    },
}


def processar_requisicao(corpo: dict) -> dict:
    if not isinstance(corpo, dict) or not isinstance(corpo.get("palestras"), list):
        raise ValueError('O corpo deve ser um objeto com a chave "palestras" (lista)')
    palestras = palestras_de_dicts(corpo["palestras"])
    janela = corpo.get("janela") or {}
    inicio = horario_para_minutos(janela["inicio"]) if "inicio" in janela else None
    fim = horario_para_minutos(janela["fim"]) if "fim" in janela else None
    return selecionar_palestras(palestras, inicio, fim).para_dict()


class _Handler(BaseHTTPRequestHandler):
    def _responder(self, status: int, dados: dict) -> None:
        conteudo = json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(conteudo)))
        self.end_headers()
        self.wfile.write(conteudo)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/agenda"):
            self._responder(200, INSTRUCOES)
        else:
            self._responder(404, {"erro": "Rota não encontrada"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/agenda":
            self._responder(404, {"erro": "Rota não encontrada"})
            return
        try:
            tamanho = int(self.headers.get("Content-Length", 0))
            corpo = json.loads(self.rfile.read(tamanho) or b"{}")
            self._responder(200, processar_requisicao(corpo))
        except json.JSONDecodeError:
            self._responder(400, {"erro": "JSON inválido"})
        except (ValueError, TypeError) as e:
            self._responder(400, {"erro": str(e)})


def servir(host: str = "127.0.0.1", porta: int = 8000) -> None:
    servidor = ThreadingHTTPServer((host, porta), _Handler)
    print(f"API rodando em http://{host}:{porta}  (Ctrl+C para encerrar)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando.")
    finally:
        servidor.server_close()
