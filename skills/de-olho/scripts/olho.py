#!/usr/bin/env python3
"""de-olho: acompanha perfis no YouTube, TikTok e Instagram e mostra o que passou da média.

Uso:
  olho.py ver <rede> <perfil> [--n 30] [--json]
  olho.py add <rede> <perfil>
  olho.py remover <rede> <perfil>
  olho.py lista
  olho.py todos [--n 30] [--json]
  olho.py checar

Redes: youtube, tiktok, instagram. YouTube e TikTok não pedem login nem chave
(usam o yt-dlp). Instagram usa a API oficial da Meta e precisa de DE_OLHO_IG_TOKEN
e DE_OLHO_IG_ID (no ambiente ou em ~/.de-olho/.env).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CASA = Path(os.environ.get("DE_OLHO_HOME", Path.home() / ".de-olho"))
LISTA = CASA / "perfis.json"
REDES = ("youtube", "tiktok", "instagram")
GRAPH = "https://graph.facebook.com/v23.0"


class Erro(Exception):
    pass


def limpar(perfil):
    perfil = perfil.strip().rstrip("/")
    if "://" in perfil:
        perfil = [p for p in urllib.parse.urlparse(perfil).path.split("/") if p][0]
    return perfil.lstrip("@")


def env(nome):
    if os.environ.get(nome):
        return os.environ[nome]
    arq = CASA / ".env"
    if arq.exists():
        for linha in arq.read_text().splitlines():
            if linha.strip().startswith(nome + "="):
                return linha.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def ytdlp(url, n):
    if not shutil.which("yt-dlp"):
        raise Erro("O yt-dlp não está instalado. Instale com: brew install yt-dlp (Mac) ou pipx install yt-dlp.")
    r = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--playlist-end", str(n), "-J", "--no-warnings", url],
        capture_output=True, text=True, timeout=180,
    )
    if r.returncode != 0 or not r.stdout.strip():
        raise Erro("Não consegui ler esse perfil: " + (r.stderr.strip().splitlines() or ["sem detalhe"])[-1][:200])
    return json.loads(r.stdout).get("entries") or []


def youtube(perfil, n):
    posts = []
    for aba in ("videos", "shorts"):
        try:
            itens = ytdlp(f"https://www.youtube.com/@{perfil}/{aba}", n)
        except Erro:
            if aba == "videos":
                raise
            continue
        for e in itens:
            if e.get("view_count") is None:
                continue
            posts.append({
                "id": e.get("id"), "tipo": "short" if aba == "shorts" else "vídeo",
                "titulo": (e.get("title") or "").strip(), "url": e.get("url") or f"https://www.youtube.com/watch?v={e.get('id')}",
                "views": e["view_count"], "metrica": e["view_count"],
            })
    return posts, "views"


def tiktok(perfil, n):
    posts = []
    for e in ytdlp(f"https://www.tiktok.com/@{perfil}", n):
        if e.get("view_count") is None:
            continue
        posts.append({
            "id": e.get("id"), "tipo": "vídeo", "titulo": (e.get("title") or e.get("description") or "").strip(),
            "url": e.get("url") or f"https://www.tiktok.com/@{perfil}/video/{e.get('id')}",
            "views": e["view_count"], "curtidas": e.get("like_count"), "comentarios": e.get("comment_count"),
            "salvos": e.get("save_count"), "data": e.get("timestamp"), "metrica": e["view_count"],
        })
    return posts, "views"


def instagram(perfil, n):
    token, ig = env("DE_OLHO_IG_TOKEN"), env("DE_OLHO_IG_ID")
    if not token or not ig:
        raise Erro(
            "Instagram precisa da API oficial da Meta. Defina DE_OLHO_IG_TOKEN e DE_OLHO_IG_ID "
            "(no ambiente ou em ~/.de-olho/.env). O passo a passo está no README."
        )
    campos = f"business_discovery.username({perfil}){{followers_count,media.limit({min(n, 50)})" \
             "{caption,media_type,media_product_type,like_count,comments_count,timestamp,permalink}}"
    url = f"{GRAPH}/{ig}?" + urllib.parse.urlencode({"fields": campos, "access_token": token})
    try:
        with urllib.request.urlopen(url, timeout=40) as r:
            dados = json.load(r)
    except urllib.error.HTTPError as e:
        msg = json.loads(e.read() or b"{}").get("error", {}).get("message", "erro da API")
        raise Erro("A API do Instagram recusou: " + msg[:200] + " (só funciona com perfil profissional).")
    posts = []
    for m in dados["business_discovery"].get("media", {}).get("data", []):
        curt, com = m.get("like_count") or 0, m.get("comments_count") or 0
        posts.append({
            "id": m.get("id"), "tipo": "reel" if m.get("media_product_type") == "REELS" else m.get("media_type", "").lower(),
            "titulo": (m.get("caption") or "").strip().split("\n")[0], "url": m.get("permalink"),
            "curtidas": curt, "comentarios": com, "data": m.get("timestamp"), "metrica": curt + 2 * com,
        })
    return posts, "curtidas + 2x comentários"


LEITORES = {"youtube": youtube, "tiktok": tiktok, "instagram": instagram}


def mediana(valores):
    v = sorted(valores)
    return v[len(v) // 2] if v else 0


def ver(rede, perfil, n):
    perfil = limpar(perfil)
    posts, metrica = LEITORES[rede](perfil, n)
    if not posts:
        raise Erro("Esse perfil não devolveu nenhum post público.")
    med = mediana(p["metrica"] for p in posts) or 1
    for p in posts:
        p["vezes"] = round(p["metrica"] / med, 1)
        p["vezes_txt"] = f"{p['vezes']:.1f}".replace(".", ",") + "x"
    CASA.mkdir(parents=True, exist_ok=True)
    arq = CASA / f"{rede}-{perfil}.json"
    antes = set(json.loads(arq.read_text()).get("ids", [])) if arq.exists() else None
    for p in posts:
        p["novo"] = antes is not None and p["id"] not in antes
    arq.write_text(json.dumps({"ids": sorted({p["id"] for p in posts} | (antes or set())), "visto": int(time.time())}))
    return {
        "rede": rede, "perfil": perfil, "metrica": metrica, "mediana": med, "primeira_vez": antes is None,
        "posts": sorted(posts, key=lambda p: -p["metrica"]),
    }


def num(v):
    if v is None:
        return "-"
    for limite, sufixo in ((1_000_000, " mi"), (1_000, " mil")):
        if v >= limite:
            return f"{v / limite:.1f}".replace(".", ",").replace(",0", "") + sufixo
    return str(v)


def texto(r, topo=8):
    linhas = [f"## {r['rede']} · @{r['perfil']}", f"{len(r['posts'])} posts lidos · mediana {num(r['mediana'])} ({r['metrica']})", ""]
    novos = [p for p in r["posts"] if p["novo"]]
    if r["primeira_vez"]:
        linhas.append("Primeira leitura desse perfil. Da próxima vez eu aviso o que é novo.")
    elif novos:
        linhas.append(f"Novos desde a última vez: {len(novos)}")
        linhas += [f"- {p['vezes_txt']} a média · {num(p['metrica'])} · {p['titulo'][:70]} · {p['url']}" for p in novos]
    else:
        linhas.append("Nada novo desde a última vez.")
    linhas += ["", "Os que mais passaram da média:"]
    linhas += [f"- {p['vezes_txt']} · {num(p['metrica'])} · {p['tipo']} · {p['titulo'][:70]} · {p['url']}" for p in r["posts"][:topo]]
    return "\n".join(linhas)


def ler_lista():
    return json.loads(LISTA.read_text()) if LISTA.exists() else []


def gravar_lista(itens):
    CASA.mkdir(parents=True, exist_ok=True)
    LISTA.write_text(json.dumps(itens, indent=1, ensure_ascii=False))


def checar():
    ok_yt = bool(shutil.which("yt-dlp"))
    ok_ig = bool(env("DE_OLHO_IG_TOKEN") and env("DE_OLHO_IG_ID"))
    print(f"YouTube e TikTok: {'prontos' if ok_yt else 'falta instalar o yt-dlp (brew install yt-dlp)'}")
    print(f"Instagram: {'configurado' if ok_ig else 'não configurado (opcional; veja o README)'}")
    print(f"Perfis na lista: {len(ler_lista())}")


def main():
    ap = argparse.ArgumentParser(description="Acompanha perfis e mostra o que passou da média.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome in ("ver", "add", "remover"):
        s = sub.add_parser(nome)
        s.add_argument("rede", choices=REDES)
        s.add_argument("perfil")
        if nome == "ver":
            s.add_argument("--n", type=int, default=30)
            s.add_argument("--json", action="store_true")
    s = sub.add_parser("todos")
    s.add_argument("--n", type=int, default=30)
    s.add_argument("--json", action="store_true")
    sub.add_parser("lista")
    sub.add_parser("checar")
    a = ap.parse_args()
    try:
        if a.cmd == "checar":
            checar()
        elif a.cmd == "lista":
            itens = ler_lista()
            print("\n".join(f"{i['rede']} @{i['perfil']}" for i in itens) or "A lista está vazia. Use: olho.py add <rede> <perfil>")
        elif a.cmd in ("add", "remover"):
            item = {"rede": a.rede, "perfil": limpar(a.perfil)}
            itens = [i for i in ler_lista() if i != item]
            if a.cmd == "add":
                itens.append(item)
            gravar_lista(itens)
            print(f"{'Adicionado' if a.cmd == 'add' else 'Removido'}: {a.rede} @{item['perfil']} ({len(itens)} na lista)")
        elif a.cmd == "ver":
            r = ver(a.rede, a.perfil, a.n)
            print(json.dumps(r, ensure_ascii=False, indent=1) if a.json else texto(r))
        elif a.cmd == "todos":
            itens = ler_lista()
            if not itens:
                raise Erro("A lista está vazia. Use: olho.py add <rede> <perfil>")
            saida = []
            for i in itens:
                try:
                    saida.append(ver(i["rede"], i["perfil"], a.n))
                except Erro as e:
                    saida.append({"rede": i["rede"], "perfil": i["perfil"], "erro": str(e)})
            if a.json:
                print(json.dumps(saida, ensure_ascii=False, indent=1))
            else:
                print("\n\n".join(texto(r) if "erro" not in r else f"## {r['rede']} · @{r['perfil']}\nNão deu: {r['erro']}" for r in saida))
    except Erro as e:
        print("Erro: " + str(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
