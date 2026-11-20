"""Instala el equipo SQP con la fábrica local. Requiere Python 3.11 o posterior."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tomllib


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(r"C:\dev\3\sports-quant-platform"),
                        help="Raíz del checkout de Sports Quant Platform.")
    parser.add_argument("--architect", type=Path, default=Path(r"C:\dev\superagent-architect"),
                        help="Raíz del checkout de superagent-architect.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Instala después de comprobar el plan.")
    mode.add_argument("--check", action="store_true", help="Comprueba el equipo ya instalado.")
    args = parser.parse_args()

    try:
        project = args.project.resolve(strict=True)
        project_metadata = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
        if project_metadata.get("project", {}).get("name") != "sqp":
            parser.error("--project debe apuntar a la raíz de Sports Quant Platform.")
        source = args.architect.resolve(strict=True) / "src"
        contract = Path(__file__).resolve().with_name("team.json")
        if not (source / "sqp_agent" / "architect_cli.py").is_file():
            parser.error("--architect debe apuntar al checkout de superagent-architect.")
        if not contract.is_file():
            parser.error("Extrae team.json junto a instalar_sqp.py.")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source))
    from sqp_agent.architect_cli import main as architect_main

    command = "team-check" if args.check else "team-build"
    cli_args = [command, str(contract), "--project", str(project)]
    if args.write:
        cli_args.append("--write")
    return architect_main(cli_args)


if __name__ == "__main__":
    raise SystemExit(main())
