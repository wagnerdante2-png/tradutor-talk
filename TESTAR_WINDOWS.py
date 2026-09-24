from __future__ import annotations

import subprocess
import sys
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"


def _run(args: list[str], *, title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)
    completed = subprocess.run(args, cwd=ROOT)
    if completed.returncode != 0:
        raise SystemExit(
            f"Falha em: {title}\n"
            f"Código de saída: {completed.returncode}"
        )


def _ensure_python() -> None:
    if sys.version_info < (3, 12):
        raise SystemExit(
            "O Tradutor Talk requer Python 3.12 ou superior.\n"
            f"Versão atual: {sys.version.split()[0]}"
        )


def _ensure_venv() -> None:
    if VENV_PYTHON.exists():
        return

    print()
    print("Criando ambiente local .venv...")
    builder = venv.EnvBuilder(with_pip=True, clear=False)
    builder.create(VENV_DIR)

    if not VENV_PYTHON.exists():
        raise SystemExit(
            "O ambiente virtual foi criado, mas o Python interno não foi encontrado."
        )


def main() -> None:
    print("=" * 72)
    print("TRADUTOR TALK — PREPARAÇÃO E TESTE WINDOWS")
    print("=" * 72)
    print()
    print("Este launcher é Python puro.")
    print("Ele não usa arquivos .bat nem altera políticas de segurança do Windows.")

    _ensure_python()
    _ensure_venv()

    _run(
        [
            str(VENV_PYTHON),
            "-m",
            "pip",
            "install",
            "-e",
            ".[dev,runtime]",
        ],
        title="Instalando/atualizando dependências locais",
    )

    _run(
        [str(VENV_PYTHON), "-m", "pytest"],
        title="Executando testes determinísticos",
    )

    _run(
        [str(VENV_PYTHON), "-m", "tradutor_talk.app.windows_test"],
        title="Abrindo assistente de teste real",
    )

    print()
    print("Teste encerrado.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuário.")
    except Exception as exc:
        print()
        print(f"ERRO: {type(exc).__name__}: {exc}")
        try:
            input("\nPressione ENTER para fechar...")
        except EOFError:
            pass
        raise
