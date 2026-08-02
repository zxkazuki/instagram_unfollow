"""
Instagram Automation — Orquestrador

Uso:
  python main.py              # Menu interativo
  python main.py login        # Salvar sessão de login
  python main.py collect      # Coletar seguidores/seguindo
  python main.py unfollow     # Executar unfollows
  python main.py all          # Coletar + Unfollow (pipeline completo)
"""

import sys
from shared import do_login, check_account, log
import get_followers
import unfollow


def show_menu() -> str:
    log("📱 Instagram Automation")
    log("=" * 50)
    print("")
    print("   1. login     — Salvar sessão (primeira vez)")
    print("   2. collect   — Coletar seguidores e seguindo")
    print("   3. unfollow  — Dar unfollow (usa dados coletados)")
    print("   4. all       — Coletar + Unfollow")
    print("   5. sair")
    print("")
    return input("   >>> Escolha (1-5 ou nome): ").strip().lower()


def run_all(username: str) -> None:
    """Pipeline completo: coleta + unfollow."""
    get_followers.run(username)
    print("\n")
    unfollow.run(username)


def main() -> None:
    # Login direto não precisa de check_account
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        do_login()
        return

    # Verifica/seleciona conta
    username = check_account()
    if not username:
        log("❌ Nenhuma conta selecionada. Saindo.")
        return
    print("")

    # Se passou argumento, executa direto
    if len(sys.argv) > 1:
        match sys.argv[1]:
            case "collect":
                get_followers.run(username)
            case "unfollow":
                unfollow.run(username)
            case "all":
                run_all(username)
            case _:
                print(f"Comando desconhecido: {sys.argv[1]}")
                print("Opções: login, collect, unfollow, all")
        return

    # Menu interativo
    choice = show_menu()
    match choice:
        case "1" | "login":
            do_login()
        case "2" | "collect":
            get_followers.run(username)
        case "3" | "unfollow":
            unfollow.run(username)
        case "4" | "all":
            run_all(username)
        case "5" | "sair" | "q":
            log("👋 Até mais!")
        case _:
            log("❌ Opção inválida.")


if __name__ == "__main__":
    main()
