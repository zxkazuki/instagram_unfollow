"""
Coleta seguidores e seguindo do Instagram.

Salva em data/{username}_results.json e data/{username}_contas.csv.
Pode ser rodado direto ou via main.py.
"""

import json
import csv
import time
from playwright.sync_api import sync_playwright

from shared import (
    log, launch_browser, is_logged_in, open_list_and_collect,
    get_results_file, get_csv_file, get_current_account, set_current_account,
)


def run(username: str | None = None) -> None:
    log("📋 Coletar seguidores e seguindo")
    log("=" * 50)

    if not username:
        username = get_current_account()
    if not username:
        username = input("   >>> Digite seu username (sem @): ").strip()
    if not username:
        log("❌ Username vazio.")
        return

    set_current_account(username)
    results_file = get_results_file(username)

    # Se já existe, pergunta se quer atualizar
    if results_file.exists():
        data = json.loads(results_file.read_text(encoding="utf-8"))
        log(f"   Dados existentes de @{username}: {len(data.get('followers', []))} seguidores, "
            f"{len(data.get('following', []))} seguindo")
        answer = input("   >>> Deseja coletar novamente? (s/n): ").strip().lower()
        if answer not in ("s", "sim", "y", "yes"):
            log("   Mantendo dados existentes.")
            return

    with sync_playwright() as pw:
        browser = launch_browser(pw)
        page = browser.pages[0] if browser.pages else browser.new_page()

        if not is_logged_in(page):
            log("❌ Não está logado! Rode: python main.py login")
            browser.close()
            return

        log(f"👤 Conta: @{username}\n")

        followers = open_list_and_collect(page, username, "followers")
        log(f"✅ Seguidores: {len(followers)}\n")
        time.sleep(3)

        following = open_list_and_collect(page, username, "following")
        log(f"✅ Seguindo: {len(following)}\n")

        browser.close()

    # Análise
    not_following_back = following - followers
    mutual = following & followers

    log("=" * 50)
    log("📊 RESULTADO:")
    log(f"   Seguindo: {len(following)}")
    log(f"   Seguidores: {len(followers)}")
    log(f"   Mútuo: {len(mutual)}")
    log(f"   NÃO seguem de volta: {len(not_following_back)}")
    log("=" * 50)

    # Salva JSON
    data = {
        "username": username,
        "following": sorted(following),
        "followers": sorted(followers),
        "mutual": sorted(mutual),
        "not_following_back": sorted(not_following_back),
    }
    results_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"💾 JSON: {results_file}")

    # Salva CSV
    csv_file = get_csv_file(username)
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "relacao"])
        for user in sorted(following | followers):
            if user in mutual:
                relacao = "mutuo"
            elif user in not_following_back:
                relacao = "nao_segue_de_volta"
            else:
                relacao = "apenas_seguidor"
            writer.writerow([user, relacao])
    log(f"💾 CSV: {csv_file}")
    log("\n✅ Coleta finalizada!")


if __name__ == "__main__":
    run()
