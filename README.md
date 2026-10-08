# de-olho

Uma skill pra agentes de código (Claude Code, Codex, Cursor e outros) que fica de olho nos perfis que você escolher e te conta duas coisas:

- **o que passou da média** daquele perfil;
- **o que é novo** desde a última vez que você olhou.

Funciona com YouTube, TikTok e Instagram.

| Rede | Precisa de login? | Precisa de chave? |
|---|---|---|
| YouTube | Não | Não |
| TikTok | Não | Não |
| Instagram | Não usa o seu login | Sim, a API oficial da Meta (configuração única) |

## Instalar

```bash
npx skills add alissonjcdev/de-olho
```

Você também precisa do [yt-dlp](https://github.com/yt-dlp/yt-dlp):

```bash
brew install yt-dlp        # Mac
pipx install yt-dlp        # Windows e Linux
```

## Usar

Peça em texto normal pro seu agente:

```text
Fica de olho no canal @fulano do YouTube e me mostra o que passou da média.
```

```text
Adiciona o @perfil do TikTok na minha lista e roda a lista inteira.
```

```text
O que meus concorrentes postaram de novo desde ontem?
```

Ou rode direto:

```bash
python3 skills/de-olho/scripts/olho.py ver youtube @fulano
python3 skills/de-olho/scripts/olho.py add tiktok @perfil
python3 skills/de-olho/scripts/olho.py todos
```

## Como ele decide o que "bombou"

Ele lê os últimos posts do perfil, calcula a mediana e divide cada post por ela. Um post "4,0x" teve quatro vezes o resultado típico daquele perfil. Comparar o perfil com ele mesmo é mais justo do que comparar perfis de tamanhos diferentes.

A métrica é views no YouTube e no TikTok. No Instagram é curtidas + 2x comentários, porque a API não entrega views de perfil de terceiro.

## Instagram (opcional)

O Instagram não deixa ler perfil sem login, e usar o seu login em ferramenta de terceiro põe a sua conta em risco. Por isso o de-olho usa só a API oficial da Meta.

Você precisa de duas coisas, uma vez só:

1. Uma conta profissional do Instagram ligada a uma Página do Facebook.
2. Um app na Meta com um token que tenha as permissões `instagram_basic` e `instagram_manage_insights`.

Depois, crie o arquivo `~/.de-olho/.env`:

```bash
DE_OLHO_IG_TOKEN=seu_token
DE_OLHO_IG_ID=id_da_sua_conta_do_instagram
```

Passo a passo com print de cada tela: [Conecte o Claude ao seu Instagram](https://alissondsgn.com.br/guias/claude-instagram).

Só dá pra ler perfis profissionais (de empresa ou de criador).

## Limites

- Só dado público. Não lê stories, mensagens nem seguidores.
- YouTube e TikTok são lidos pelo yt-dlp, que acompanha as mudanças das páginas. Se parar de funcionar, atualize o yt-dlp.
- Respeite os termos de cada plataforma e use pra pesquisa, não pra copiar o conteúdo dos outros.
- A lista de perfis e o histórico ficam em `~/.de-olho/` no seu computador.

## Licença

MIT
