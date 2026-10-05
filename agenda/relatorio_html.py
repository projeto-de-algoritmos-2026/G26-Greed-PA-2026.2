"""Relatório em HTML (página única, sem dependências) para abrir no navegador."""

from __future__ import annotations

from html import escape

from .algoritmo import ResultadoAgenda
from .modelos import Palestra, minutos_para_horario
from .visualizacao import formatar_duracao

ESTILO = """
:root { --fundo:#f6f7f9; --cartao:#fff; --texto:#1d2330; --suave:#6b7280; --borda:#e3e6eb;
        --ok:#2f9e66; --ok-claro:#d8f3e5; --nao:#d64545; --nao-claro:#fbe1e1; --trilho:#eef0f3; }
@media (prefers-color-scheme: dark) {
  :root { --fundo:#14171c; --cartao:#1d2128; --texto:#e7e9ee; --suave:#9aa3b2; --borda:#2c323c;
          --ok:#3fbf80; --ok-claro:#1d3a2c; --nao:#ef6464; --nao-claro:#422326; --trilho:#272c34; }
}
* { box-sizing: border-box; }
body { margin:0; padding:24px 16px; background:var(--fundo); color:var(--texto);
       font:15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1000px; margin: 0 auto; }
h1 { margin:0 0 4px; font-size:24px; }
h2 { font-size:17px; margin:0 0 12px; }
.sub { color:var(--suave); margin:0 0 20px; }
.cartao { background:var(--cartao); border:1px solid var(--borda); border-radius:10px;
          padding:18px; margin-bottom:18px; }
.metricas { display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:12px; }
.metrica { background:var(--cartao); border:1px solid var(--borda); border-radius:10px; padding:14px; }
.metrica .rotulo { color:var(--suave); font-size:13px; }
.metrica .valor { font-size:24px; font-weight:650; font-variant-numeric:tabular-nums; }
.barra-ocupacao { height:10px; background:var(--trilho); border-radius:5px; overflow:hidden; margin-top:6px; }
.barra-ocupacao span { display:block; height:100%; background:var(--ok); }
.gantt { display:grid; grid-template-columns:minmax(120px, 230px) 1fr; gap:6px 12px; align-items:center; }
.gantt .nome { font-size:13px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.trilho { position:relative; height:22px; background:var(--trilho); border-radius:4px; }
.bloco { position:absolute; top:0; bottom:0; border-radius:4px; font-size:11px; color:#fff;
         padding:0 6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; line-height:22px;
         box-shadow:inset -1px 0 0 var(--cartao); }
.bloco.ok { background:var(--ok); }
.bloco.nao { background:var(--nao-claro); color:var(--nao); border:1px dashed var(--nao); }
.sala .trilho { height:30px; }
.sala .bloco { line-height:30px; }
.regua { position:relative; height:18px; color:var(--suave); font-size:12px;
         font-variant-numeric:tabular-nums; }
.regua span { position:absolute; transform:translateX(-50%); white-space:nowrap; }
.legenda { display:flex; gap:16px; color:var(--suave); font-size:13px; margin-top:12px; }
.legenda i { display:inline-block; width:12px; height:12px; border-radius:3px; vertical-align:-1px; margin-right:5px; }
.tabela { overflow-x:auto; }
table { width:100%; border-collapse:collapse; font-size:14px; }
th, td { text-align:left; padding:8px 10px; border-bottom:1px solid var(--borda); vertical-align:top; }
th { color:var(--suave); font-weight:600; font-size:13px; }
td.hora { font-variant-numeric:tabular-nums; white-space:nowrap; }
.tag { display:inline-block; padding:1px 8px; border-radius:10px; font-size:12px; font-weight:600; }
.tag.ok { background:var(--ok-claro); color:var(--ok); }
.tag.nao { background:var(--nao-claro); color:var(--nao); }
@media (max-width: 600px) { .gantt { grid-template-columns: 1fr; } .gantt .nome { margin-top:6px; } }
"""


def _bloco(p: Palestra, r: ResultadoAgenda, classe: str, texto: str = "") -> str:
    total = r.tempo_janela or 1
    esquerda = max(0.0, (p.inicio - r.janela_inicio) / total * 100)
    largura = max(0.5, min(p.fim, r.janela_fim) - max(p.inicio, r.janela_inicio)) / total * 100
    dica = escape(f"{p.titulo} — {p.inicio_str}–{p.fim_str}")
    return (f'<div class="bloco {classe}" style="left:{esquerda:.2f}%;width:{largura:.2f}%" '
            f'title="{dica}">{escape(texto)}</div>')


def _regua(r: ResultadoAgenda) -> str:
    """Marcas nas horas cheias (de 1 em 1h, ou de 2 em 2h em eventos longos)."""
    if not r.tempo_janela:
        return '<div class="regua"></div>'
    passo = 60 if r.tempo_janela <= 12 * 60 else 120
    primeira = -(-r.janela_inicio // passo) * passo  # arredonda para cima
    marcas = []
    for minuto in range(primeira, r.janela_fim + 1, passo):
        pos = (minuto - r.janela_inicio) / r.tempo_janela * 100
        # Evita que os rótulos das pontas saiam do trilho.
        ajuste = "transform:none;" if pos < 3 else "transform:translateX(-100%);" if pos > 97 else ""
        marcas.append(f'<span style="left:{pos:.2f}%;{ajuste}">{minutos_para_horario(minuto)}</span>')
    return '<div class="regua">' + "".join(marcas) + "</div>"


def _motivo(p: Palestra, r: ResultadoAgenda) -> str:
    conflitos = r.conflitos.get(p, [])
    if not conflitos:
        return "Fora da janela do evento"
    return "Conflita com: " + ", ".join(
        f"<strong>{escape(c.titulo)}</strong> ({c.inicio_str}–{c.fim_str})" for c in conflitos
    )


def gerar_html(r: ResultadoAgenda, titulo: str = "Grade de Palestras") -> str:
    total = len(r.aceitas) + len(r.rejeitadas)
    pct = r.taxa_ocupacao * 100
    aceitas = set(r.aceitas)
    todas = sorted([*r.aceitas, *r.rejeitadas], key=lambda p: (p.inicio, p.fim))

    linhas_gantt = "".join(
        f'<div class="nome" title="{escape(p.titulo)}">{escape(p.titulo)}</div>'
        f'<div class="trilho">{_bloco(p, r, "ok" if p in aceitas else "nao", f"{p.inicio_str}–{p.fim_str}")}</div>'
        for p in todas
    )
    sala = "".join(_bloco(p, r, "ok", p.titulo) for p in r.aceitas)

    linhas_aceitas = "".join(
        f'<tr><td>{i}</td><td class="hora">{p.inicio_str}–{p.fim_str}</td>'
        f"<td>{formatar_duracao(p.duracao)}</td><td>{escape(p.titulo)}</td>"
        f"<td>{escape(p.palestrante or '—')}</td></tr>"
        for i, p in enumerate(r.aceitas, start=1)
    ) or '<tr><td colspan="5">Nenhuma palestra aceita.</td></tr>'

    linhas_rejeitadas = "".join(
        f'<tr><td class="hora">{p.inicio_str}–{p.fim_str}</td><td>{escape(p.titulo)}</td>'
        f"<td>{_motivo(p, r)}</td></tr>"
        for p in r.rejeitadas
    ) or '<tr><td colspan="3">Nenhuma palestra rejeitada.</td></tr>'

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(titulo)}</title>
<style>{ESTILO}</style>
</head>
<body>
<main>
  <h1>{escape(titulo)}</h1>
  <p class="sub">Sala única · janela do evento {minutos_para_horario(r.janela_inicio)}–{minutos_para_horario(r.janela_fim)}
     · {total} propostas recebidas</p>

  <section class="metricas cartao" style="background:none;border:0;padding:0">
    <div class="metrica"><div class="rotulo">Palestras aceitas</div>
      <div class="valor">{len(r.aceitas)} <span class="tag ok">de {total}</span></div></div>
    <div class="metrica"><div class="rotulo">Palestras rejeitadas</div>
      <div class="valor">{len(r.rejeitadas)}</div></div>
    <div class="metrica"><div class="rotulo">Tempo aproveitado</div>
      <div class="valor">{formatar_duracao(r.tempo_ocupado)}</div></div>
    <div class="metrica"><div class="rotulo">Tempo ocioso</div>
      <div class="valor">{formatar_duracao(r.tempo_ocioso)}</div></div>
    <div class="metrica"><div class="rotulo">Ocupação da sala</div>
      <div class="valor">{pct:.1f}%</div>
      <div class="barra-ocupacao"><span style="width:{pct:.1f}%"></span></div></div>
  </section>

  <section class="cartao sala">
    <h2>Grade final da sala</h2>
    <div class="gantt">
      <div class="nome"><strong>Sala</strong></div><div class="trilho">{sala}</div>
      <div></div>{_regua(r)}
    </div>
  </section>

  <section class="cartao">
    <h2>Todas as propostas</h2>
    <div class="gantt">{linhas_gantt}<div></div>{_regua(r)}</div>
    <div class="legenda"><span><i style="background:var(--ok)"></i>Aceita</span>
      <span><i style="background:var(--nao-claro);border:1px dashed var(--nao)"></i>Rejeitada</span></div>
  </section>

  <section class="cartao">
    <h2><span class="tag ok">✔</span> Palestras aceitas ({len(r.aceitas)})</h2>
    <div class="tabela"><table>
      <tr><th>#</th><th>Horário</th><th>Duração</th><th>Título</th><th>Palestrante</th></tr>
      {linhas_aceitas}
    </table></div>
  </section>

  <section class="cartao">
    <h2><span class="tag nao">✘</span> Palestras rejeitadas ({len(r.rejeitadas)})</h2>
    <div class="tabela"><table>
      <tr><th>Horário</th><th>Título</th><th>Motivo</th></tr>
      {linhas_rejeitadas}
    </table></div>
  </section>
</main>
</body>
</html>
"""
