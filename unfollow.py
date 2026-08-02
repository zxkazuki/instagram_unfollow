"""
Instagram Unfollow — lê results.json e faz unfollow nas contas que não seguem de volta.

Pode ser rodado direto ou via main.py.
"""

import random
import json
import time
from playwright.sync_api import sync_playwright, Page

from shared import log, launch_browser, is_logged_in, get_results_file, get_current_account

# --- Configuração ---
MAX_UNFOLLOWS_RANGE = (55, 80)     # Limite aleatório por sessão
FAST_PHASE_LIMIT = 30              # Primeiros 30 unfollows são rápidos
FAST_DELAY = (3, 7)                # 3-7s entre unfollows rápidos
SLOW_DELAY = (30, 90)              # 30-90s após o limite de fase rápida


def smart_delay(unfollow_count: int) -> None:
    """Delay curto nos primeiros 30, longo depois."""
    if unfollow_count < FAST_PHASE_LIMIT:
        delay = random.uniform(*FAST_DELAY)
        log(f"⏳ Aguardando {delay:.0f}s...")
    else:
        delay = random.uniform(*SLOW_DELAY)
        log(f"⏳ Fase lenta — aguardando {delay:.0f}s...")
    time.sleep(delay)


def unfollow_user(page: Page, username: str) -> bool:
    """Acessa perfil e faz unfollow."""
    try:
        page.goto(f"https://www.instagram.com/{username}/", wait_until="domcontentloaded")
        time.sleep(2)

        btn = page.query_selector("button:has-text('Seguindo')") or \
              page.query_selector("button:has-text('Following')") or \
              page.query_selector("div[role='button']:has-text('Seguindo')") or \
              page.query_selector("div[role='button']:has-text('Following')")

        if not btn:
            log(f"  ⚠️  Botão 'Seguindo' não encontrado para @{username}")
            return False

        btn.click()
        time.sleep(3)

        # Espera botão de confirmação aparecer
        confirm = None
        for _ in range(5):
            confirm = page.query_selector("button:has-text('Deixar de seguir')") or \
                      page.query_selector("button:has-text('Unfollow')") or \
                      page.query_selector("span:has-text('Deixar de seguir')") or \
                      page.query_selector("span:has-text('Unfollow')") or \
                      page.query_selector("div[role='button']:has-text('Deixar de seguir')") or \
                      page.query_selector("div[role='button']:has-text('Unfollow')")
            if confirm:
                break
            time.sleep(1)

        if not confirm:
            try:
                page.locator("text=Deixar de seguir").or_(
                    page.locator("text=Unfollow")
                ).first.click(timeout=5000)
                time.sleep(1)
                return True
            except Exception:
                log(f"  ⚠️  Botão 'Deixar de seguir' não apareceu para @{username}")
                return False

        confirm.click()
        time.sleep(1)
        return True

    except Exception as e:
        log(f"  ⚠️  Erro em @{username}: {e}")
        return False


def run(username: str | None = None) -> None:
    log("🚀 Instagram Unfollow")
    log("=" * 50)

    if not username:
        username = get_current_account()
    if not username:
        log("❌ Nenhuma conta configurada! Rode: python main.py")
        return

    results_file = get_results_file(username)
    if not results_file.exists():
        log(f"❌ {results_file.name} não encontrado!")
        log("   Rode primeiro: python main.py collect")
        return

    data = json.loads(results_file.read_text(encoding="utf-8"))
    targets = data.get("not_following_back", [])

    if not targets:
        log("🎉 Lista vazia! Nada a fazer.")
        return

    log(f"📋 {len(targets)} contas que não seguem de volta\n")

    session_limit = random.randint(*MAX_UNFOLLOWS_RANGE)
    log(f"⚠️  Limite desta sessão: {session_limit} (aleatório {MAX_UNFOLLOWS_RANGE[0]}-{MAX_UNFOLLOWS_RANGE[1]})")
    log(f"   Primeiros {FAST_PHASE_LIMIT}: rápido (3-7s). Depois: lento (30-90s).")
    confirm = input("   >>> Prosseguir? (s/n): ").strip().lower()
    if confirm not in ("s", "sim", "y", "yes"):
        log("❌ Cancelado.")
        return

    with sync_playwright() as pw:
        browser = launch_browser(pw)
        page = browser.pages[0] if browser.pages else browser.new_page()

        if not is_logged_in(page):
            log("❌ Não está logado! Rode: python main.py login")
            browser.close()
            return

        log("\n🔄 Iniciando unfollows...\n")
        success = 0
        fail = 0
        unfollowed: list[str] = []

        for i, user in enumerate(targets, 1):
            if success >= session_limit:
                log(f"🛑 Limite de {session_limit} atingido. Rode amanhã.")
                break

            log(f"[{i}/{len(targets)}] @{user}...")
            if unfollow_user(page, user):
                success += 1
                unfollowed.append(user)
                log("  ✅ Feito!")
            else:
                fail += 1

            if i < len(targets) and success < session_limit:
                smart_delay(success)

        browser.close()

    # Atualiza JSON removendo quem foi unfollowed
    remaining = [u for u in targets if u not in unfollowed]
    data["not_following_back"] = remaining
    results_file = get_results_file(username)
    results_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    log("\n" + "=" * 50)
    log("📊 RESUMO:")
    log(f"   ✅ Unfollows: {success}")
    log(f"   ❌ Falhas: {fail}")
    log(f"   📋 Restantes: {len(remaining)}")
    log("=" * 50)


if __name__ == "__main__":
    run()
