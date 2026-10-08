---
name: de-olho
description: Acompanha perfis de concorrentes e referências no YouTube, TikTok e Instagram e mostra quais posts passaram da média do próprio perfil, e o que é novo desde a última checagem. Use quando a pessoa pedir pra ficar de olho num concorrente, ver o que está bombando num perfil, achar os posts fora da curva de um canal, comparar perfis ou montar uma lista de perfis pra acompanhar.
---

# de-olho

Lê os posts públicos de um perfil e responde duas perguntas: **o que passou da média dele** e **o que é novo desde a última vez**.

- YouTube e TikTok: sem login e sem chave (usa o `yt-dlp`).
- Instagram: pela API oficial da Meta. Precisa de configuração uma vez (veja "Instagram" abaixo). Só lê perfil profissional.

O script fica em `scripts/olho.py` dentro da pasta desta skill. Rode sempre com `python3`.

## Antes da primeira vez

Rode `python3 scripts/olho.py checar`. Ele diz se o `yt-dlp` está instalado e se o Instagram está configurado.
Se faltar o `yt-dlp`, peça permissão e instale: `brew install yt-dlp` no Mac, ou `pipx install yt-dlp`.

## Comandos

```bash
python3 scripts/olho.py ver youtube @canal          # um perfil, agora
python3 scripts/olho.py ver tiktok @perfil
python3 scripts/olho.py ver instagram perfil
python3 scripts/olho.py add youtube @canal          # põe na lista de perfis acompanhados
python3 scripts/olho.py lista
python3 scripts/olho.py todos                        # roda a lista inteira
python3 scripts/olho.py remover youtube @canal
```

Opções: `--n 30` (quantos posts ler, padrão 30) e `--json` (saída estruturada, se você for cruzar perfis).
O perfil pode vir como `@nome`, `nome` ou o link do perfil.

## Como responder

1. Diga quantos posts leu e qual é a mediana do perfil.
2. Se houver posts novos desde a última checagem, mostre esses primeiro.
3. Liste os que mais passaram da média, com o número de vezes, o título e o link.
4. Feche com o padrão que você enxerga nos que passaram da média (tema, formato, tipo de título). Só afirme o que os dados mostram.

"Vezes a média" é a métrica do post dividida pela mediana do perfil. A métrica é views no YouTube e no TikTok, e curtidas + 2x comentários no Instagram (a API não entrega views de perfil de terceiro).

## Instagram

Sem `DE_OLHO_IG_TOKEN` e `DE_OLHO_IG_ID` o script avisa e para. Não tente contornar com raspagem nem com o login da pessoa.
Explique que é uma configuração única pela API oficial e aponte o README, que tem o passo a passo. As duas variáveis podem ficar no ambiente ou em `~/.de-olho/.env`.

## Limites

- Só dado público. Não lê stories, mensagens nem lista de seguidores.
- O `yt-dlp` depende das páginas do YouTube e do TikTok. Se um deles mudar, atualize o `yt-dlp` antes de concluir que quebrou.
- A lista e o histórico ficam em `~/.de-olho/`. Nada é enviado pra fora além das consultas às próprias redes.
