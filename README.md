# Instagram Unfollow Automation

Script que identifica contas que não te seguem de volta no Instagram e faz unfollow automático com delays aleatórios para evitar banimento.

## Setup (PC novo)

### 1. Instalar Python 3.11+

Baixe em https://www.python.org/downloads/ e instale marcando **"Add to PATH"**.

### 2. Instalar dependências

```bash
pip install playwright
python -m playwright install firefox
```

### 3. Clonar/copiar o projeto

```bash
cd pasta-onde-quer
git clone <url-do-repo>
cd instagram-unfollow
```

### 4. Primeiro uso — fazer login

```bash
python main.py login
```

O Firefox vai abrir. Faça login no Instagram manualmente, depois volte ao terminal e digite `ok`.

### 5. Pronto — agora pode usar

```bash
python main.py
```

## Comandos

| Comando | O que faz |
|---------|-----------|
| `python main.py` | Menu interativo |
| `python main.py login` | Salvar sessão de login no browser |
| `python main.py collect` | Coletar seguidores e seguindo |
| `python main.py unfollow` | Executar unfollows (usa dados coletados) |
| `python main.py all` | Coletar + Unfollow (pipeline completo) |

## Fluxo de uso diário

```
python main.py        → confirma conta → escolhe "unfollow" → confirma → deixa rodar
```

No dia seguinte, roda de novo. O script continua de onde parou (atualiza o JSON removendo quem já foi unfollowed).

## Trocar de conta

Ao rodar `python main.py`, o script pergunta:

```
👤 Conta atual: @igor_kazuki
   >>> Continuar com essa conta? (s/n):
```

Digita `n` → faz logout/login no browser com a nova conta → informa o username.  
Os dados da conta anterior ficam salvos em `data/` e não são perdidos.

## Estrutura de dados

```
data/
├── igor_kazuki_results.json    # Seguidores, seguindo, análise
├── igor_kazuki_contas.csv      # CSV com todas as contas e relação
├── kahinokuma_results.json     # Outra conta
└── kahinokuma_contas.csv
```

## Segurança

- **Login manual** — credenciais nunca são digitadas pelo script
- **Firefox** — menos detecção de automação que Chromium
- **Delays aleatórios** — 3-7s nos primeiros 30, depois 30-90s
- **Limite aleatório por sessão** — entre 55 e 80 unfollows
- **100% local** — nenhum dado sai da máquina
- **Sessão persistente** — `browser_data/` mantém login entre execuções

## Configuração

Edite as constantes no topo de `unfollow.py`:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `MAX_UNFOLLOWS_RANGE` | (55, 80) | Limite aleatório de unfollows por sessão |
| `FAST_PHASE_LIMIT` | 30 | Quantidade de unfollows na fase rápida |
| `FAST_DELAY` | (3, 7) | Intervalo em segundos na fase rápida |
| `SLOW_DELAY` | (30, 90) | Intervalo em segundos na fase lenta |

## Troubleshooting

| Problema | Solução |
|----------|---------|
| `ModuleNotFoundError: playwright` | Rode `pip install playwright` |
| Browser não abre | Rode `python -m playwright install firefox` |
| reCAPTCHA / tela em branco | Delete `browser_data/` e rode `python main.py login` de novo |
| Instagram bloqueou ações | Espere 24-48h e reduza `MAX_UNFOLLOWS_RANGE` |
| Scroll não funciona no modal | Feche o script, delete `browser_data/`, rode login de novo |
