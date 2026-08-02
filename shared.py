"""Funções compartilhadas entre os scripts de automação do Instagram."""

import sys
import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, BrowserContext

SCROLL_PAUSE_SECONDS = 2.0
BROWSER_DATA_DIR = Path(__file__).parent / "browser_data"
DATA_DIR = Path(__file__).parent / "data"
ACCOUNT_FILE = Path(__file__).parent / "current_account.txt"


def get_results_file(username: str) -> Path:
    """Retorna path do results.json para o username."""
    DATA_DIR.mkdir(exist_ok=True)
    return DATA_DIR / f"{username}_results.json"


def get_csv_file(username: str) -> Path:
    """Retorna path do CSV para o username."""
    DATA_DIR.mkdir(exist_ok=True)
    return DATA_DIR / f"{username}_contas.csv"


def get_current_account() -> str | None:
    """Lê a conta ativa salva."""
    if not ACCOUNT_FILE.exists():
        return None
    return ACCOUNT_FILE.read_text(encoding="utf-8").strip() or None


def set_current_account(username: str) -> None:
    """Salva a conta ativa."""
    ACCOUNT_FILE.write_text(username, encoding="utf-8")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def check_account() -> str | None:
    """Verifica qual conta está ativa e pergunta se quer trocar. Retorna o username."""
    current_user = get_current_account()

    if current_user:
        log(f"👤 Conta atual: @{current_user}")
        answer = input("   >>> Continuar com essa conta? (s/n): ").strip().lower()
        if answer in ("s", "sim", "y", "yes", ""):
            return current_user
        # Quer trocar — pede login
        log("   O navegador vai abrir — faça logout e login na nova conta.")
        do_login()
        new_user = input("   >>> Username da nova conta (sem @): ").strip()
        if new_user:
            set_current_account(new_user)
            return new_user
        return None

    # Nenhuma conta — pede primeira vez
    log("👤 Nenhuma conta configurada.")
    answer = input("   >>> Deseja fazer login? (s/n): ").strip().lower()
    if answer not in ("s", "sim", "y", "yes"):
        return None
    do_login()
    new_user = input("   >>> Username da conta (sem @): ").strip()
    if new_user:
        set_current_account(new_user)
        return new_user
    return None


def launch_browser(pw) -> BrowserContext:
    """Lança Firefox com contexto persistente (mantém login)."""
    return pw.firefox.launch_persistent_context(
        str(BROWSER_DATA_DIR),
        headless=False,
        viewport={"width": 1280, "height": 800},
        locale="pt-BR",
    )


def is_logged_in(page: Page) -> bool:
    """Verifica se o usuário está logado no Instagram."""
    try:
        page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=30000)
        time.sleep(6)
    except Exception:
        return False

    if page.query_selector("input[name='username']"):
        return False
    if "login" in page.url.lower() or "accounts" in page.url.lower():
        return False
    return True


def do_login() -> None:
    """Abre browser, espera login manual, salva sessão."""
    log("🔐 MODO LOGIN — Salvar sessão do Instagram")
    log("=" * 50)

    with sync_playwright() as pw:
        browser = launch_browser(pw)
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto("https://www.instagram.com/", wait_until="domcontentloaded")

        log("")
        log("🔐 O NAVEGADOR ESTÁ ABERTO.")
        log("   1. Faça login normalmente no Instagram")
        log("   2. Aguarde a página inicial carregar (feed)")
        log("   3. Volte aqui e digite 'ok'")
        log("")
        log("   ⚠️  NÃO feche o navegador!")
        log("")

        while True:
            answer = input("   >>> Digite 'ok' quando terminar (ou 'sair'): ").strip().lower()
            if answer in ("ok", "s", "sim"):
                log("✅ Sessão salva!")
                break
            if answer in ("sair", "q", "quit"):
                log("❌ Cancelado.")
                browser.close()
                sys.exit(0)
            log("   Digite 'ok' ou 'sair'.")

        browser.close()


def scroll_modal_and_collect(page: Page) -> set[str]:
    """Rola o modal aberto e coleta usernames."""
    usernames: set[str] = set()
    stale_rounds = 0

    find_scrollable_js = """
    () => {
        const dialog = document.querySelector('div[role="dialog"]');
        if (!dialog) return null;
        const elements = dialog.querySelectorAll('div');
        for (const el of elements) {
            if (el.scrollHeight > el.clientHeight + 50 && el.clientHeight > 100) {
                return el;
            }
        }
        return dialog;
    }
    """
    scrollable = page.evaluate_handle(find_scrollable_js)

    ignored = ("explore", "reels", "p", "stories", "accounts", "direct", "tags")

    while stale_rounds < 8:
        links = page.query_selector_all("div[role='dialog'] a[href^='/']")
        prev_count = len(usernames)

        for link in links:
            href = link.get_attribute("href") or ""
            parts = href.strip("/").split("/")
            if len(parts) == 1 and parts[0] and parts[0] not in ignored:
                usernames.add(parts[0])

        stale_rounds = stale_rounds + 1 if len(usernames) == prev_count else 0
        log(f"  Coletados: {len(usernames)} contas...")

        try:
            scrollable.evaluate("el => { if(el) el.scrollTop = el.scrollHeight; }")
        except Exception:
            page.keyboard.press("End")

        time.sleep(SCROLL_PAUSE_SECONDS)

    return usernames


def open_list_and_collect(page: Page, username: str, list_type: str) -> set[str]:
    """Navega ao perfil, abre a lista (followers/following) e coleta."""
    label_pt = "seguidores" if list_type == "followers" else "seguindo"
    log(f"📋 Coletando {label_pt}...")

    page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded")
    time.sleep(4)

    href_part = f"/{username}/{list_type}/"
    link = page.query_selector(f"a[href='{href_part}']") or \
           page.query_selector(f"a[href*='/{list_type}']")

    if link:
        link.click()
    else:
        log(f"  Tentando clicar por texto '{label_pt}'...")
        page.get_by_role("link", name=label_pt).or_(
            page.get_by_role("link", name=list_type)
        ).click()

    time.sleep(4)

    try:
        page.wait_for_selector("div[role='dialog']", timeout=15000)
    except Exception:
        log(f"  ❌ Modal de {label_pt} não apareceu!")
        return set()

    time.sleep(2)
    return scroll_modal_and_collect(page)
