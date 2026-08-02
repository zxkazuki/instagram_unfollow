# Instagram Unfollow Automation

Script Playwright que identifica contas que não te seguem de volta e faz unfollow automático com delays aleatórios.

## Instalação

```bash
cd instagram-unfollow
pip install -r requirements.txt
playwright install firefox
```

## Uso

```bash
# 1. Primeiro uso — faz login manual e salva a sessão
python unfollow.py login

# 2. Coleta seguidores/seguindo e salva em data/{username}_results.json + data/{username}_contas.csv
python unfollow.py collect
# ou via módulo separado:
python get_followers.py

# 3. Executa unfollows a partir do results da conta ativa
python unfollow.py
```

## Fluxo

1. **Login (uma vez):** `python unfollow.py login` abre o Chromium, você faz login manual, e digita `ok` no terminal para salvar a sessão
2. **Troca de conta:** ao iniciar, o script verifica qual conta está em `current_account.txt`. Se quiser trocar, ele abre o browser para novo login e salva a nova conta
3. **Coleta:** `python unfollow.py collect` pede seu username, coleta **seguindo** e **seguidores**, compara e salva em `data/{username}_results.json` + `data/{username}_contas.csv`
4. **Unfollow:** `python unfollow.py` lê o results do username ativo, mostra quantas contas não seguem de volta, pede confirmação e executa unfollows
5. Após cada sessão, o results é atualizado removendo as contas já unfollowed
6. Rode `python unfollow.py` novamente para continuar de onde parou (idempotente)
7. **Multi-conta:** cada conta tem seus próprios arquivos de dados — trocar de conta não apaga dados anteriores

## Estrutura

| Arquivo | Responsabilidade |
|---------|-----------------|
| `unfollow.py` | Script original monolítico (login + coleta + unfollow) |
| `shared.py` | Funções utilitárias compartilhadas (browser, login, scroll, coleta, troca de conta) |
| `get_followers.py` | Módulo isolado de coleta (importável ou executável direto) |

## Arquivos de Saída

Os dados são armazenados por conta na pasta `data/`:

| Arquivo | Conteúdo |
|---------|----------|
| `current_account.txt` | Username da conta ativa |
| `data/{username}_results.json` | Listas completas (following, followers, mutual, not_following_back) |
| `data/{username}_contas.csv` | Todas as contas com coluna `relacao`: `mutuo`, `nao_segue_de_volta`, ou `apenas_seguidor` |

## Segurança

- **Login separado** — rode `python unfollow.py login` uma vez para salvar a sessão
- **Troca de conta** — cada conta tem seus dados isolados em `data/`; trocar não apaga nada
- **Credenciais nunca são digitadas pelo script** — login é 100% manual no navegador
- **Smart delay em duas fases** — primeiros 30 unfollows com delay curto (3-7s), depois delay longo (30-90s)
- **Limite por sessão** — entre 55-80 unfollows aleatórios (configurável no código)
- **100% local** — nenhum dado sai da sua máquina
- **Sessão persistente** — pasta `browser_data/` mantém o login entre execuções
- **Anti-detecção** — usa Firefox (sem flags de automação expostas, fingerprint mais limpo que Chromium)

## Configuração

Edite as constantes no topo de `unfollow.py`:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `MAX_UNFOLLOWS_RANGE` | (55, 80) | Limite aleatório de unfollows por sessão |
| `FAST_PHASE_LIMIT` | 30 | Quantidade de unfollows na fase rápida |
| `FAST_DELAY` | (3, 7) | Intervalo de delay em segundos na fase rápida |
| `SLOW_DELAY` | (30, 90) | Intervalo de delay em segundos na fase lenta |
| `SCROLL_PAUSE_SECONDS` | 2.0 | Pausa entre scrolls na coleta de listas |
