# agent-architect:generated team=sqp-superagent version=1.0.0
# Hook PreToolUse de Claude Code: bloquea escrituras fuera del write_scope del rol.
# Falla cerrado: cualquier error bloquea (exit 2). No editar: regenerar con team-build.
"""Guardián de escritura por rol (autónomo: sin dependencias del paquete).

El código fuente de este módulo se incrusta en los artefactos generados (hook
de Claude Code y runtime del OpenAI Agents SDK), por eso solo usa la biblioteca
estándar y no importa nada de sqp_agent.

Semántica de patrones (anclados en la raíz del proyecto):
  *   cualquier secuencia dentro de un segmento
  ?   un carácter dentro de un segmento
  **  cero o más segmentos completos
Las comparaciones no distinguen mayúsculas (Windows/macOS).
"""
from __future__ import annotations

import fnmatch
import os

# Segmentos que pueden contener secretos: ni se leen ni se escriben.
GUARD_SECRET_SEGMENTS = (
    ".mcp.json", ".env", ".env.*", ".ssh", ".aws", ".gnupg", "secrets",
    "*.pem", "*.key", "*.p12", "*.pfx", "id_rsa*", "id_dsa*", "id_ecdsa*", "id_ed25519*",
    ".npmrc", ".netrc", ".pypirc", "credentials*",
)
# Archivos concretos con credenciales habituales dentro de zonas legibles.
GUARD_SECRET_FILES = (".git/config", ".claude/settings.local.json", ".codex/config.toml")
# Segmentos que ningún rol puede escribir (en minúsculas): secretos, git,
# configuración y agentes de las plataformas, memoria y contrato del equipo,
# instrucciones persistentes de agentes y automatismos que ejecutan código.
GUARD_PROTECTED_SEGMENTS = (
    ".git", ".claude", ".codex", ".superagente",
    "claude.md", "claude.local.md", "agents.md", "agents.override.md",
    ".github", ".gitlab-ci.yml", ".husky", ".githooks", ".vscode", ".idea",
) + GUARD_SECRET_SEGMENTS


def _split(path: str) -> list[str]:
    return [s for s in path.replace("\\", "/").split("/") if s not in ("", ".")]


def _match_segments(pat: list[str], parts: list[str]) -> bool:
    if not pat:
        return not parts
    head = pat[0]
    if head == "**":
        return any(_match_segments(pat[1:], parts[i:]) for i in range(len(parts) + 1))
    return bool(parts) and fnmatch.fnmatchcase(parts[0], head) and _match_segments(pat[1:], parts[1:])


def match_scope(rel_path: str, patterns: list[str] | tuple[str, ...]) -> bool:
    parts = [p.casefold() for p in _split(rel_path)]
    return any(_match_segments([s.casefold() for s in _split(p)], parts) for p in patterns)


def is_protected(rel_path: str) -> str | None:
    parts = [p.casefold() for p in _split(rel_path)]
    for part in parts:
        for name in GUARD_PROTECTED_SEGMENTS:
            if fnmatch.fnmatchcase(part, name):
                return name
    return None


def relative_inside(project_root: str, path: str) -> str | None:
    """Ruta relativa (con '/') si `path` queda dentro del proyecto; si no, None.

    Resuelve enlaces simbólicos para que un enlace dentro del proyecto no
    permita escribir fuera.
    """
    root = os.path.realpath(project_root)
    target = path if os.path.isabs(path) else os.path.join(root, path)
    target = os.path.realpath(target)
    try:
        common = os.path.commonpath([os.path.normcase(root), os.path.normcase(target)])
    except ValueError:  # distinta unidad en Windows
        return None
    if common != os.path.normcase(root):
        return None
    rel = os.path.relpath(target, root)
    return None if rel == "." else rel.replace(os.sep, "/")


def _ambiguous_segment(*paths: str) -> str | None:
    """Primer segmento que Windows interpretaría distinto de como se compara:
    flujos alternativos (`a:b`, `.env::$DATA`) o puntos/espacios finales que
    el sistema elimina al abrir (`.env.`, `.env `). Se miran la ruta pedida y
    la resuelta, porque la resolución no siempre los normaliza. La unidad de
    una ruta absoluta (`C:`) no cuenta."""
    for p in paths:
        _, rest = os.path.splitdrive(p)
        for seg in _split(rest):
            if seg == "..":  # lo resuelve `relative_inside`
                continue
            if ":" in seg or seg.endswith((".", " ")):
                return seg
    return None


def write_denial(project_root: str, path: str, patterns: list[str] | tuple[str, ...],
                 *, exact: list[str] | tuple[str, ...] = ()) -> str | None:
    """Motivo para bloquear una escritura, o None si está permitida.

    `exact` son rutas relativas concretas permitidas aunque estén en una zona
    protegida (p. ej. la memoria del coordinador en .superagente/).
    """
    if not isinstance(path, str) or not path.strip():
        return "ruta vacía"
    rel = relative_inside(project_root, path)
    if rel is None:
        return f"'{path}' está fuera del proyecto"
    seg = _ambiguous_segment(path, rel)
    if seg is not None:
        return f"segmento ambiguo '{seg}'"
    if rel.casefold() in {"/".join(_split(e)).casefold() for e in exact}:
        return None
    hit = is_protected(rel)
    if hit:
        return f"'{rel}' es una ruta protegida ({hit})"
    if not match_scope(rel, patterns):
        return f"'{rel}' está fuera del write_scope del rol ({', '.join(patterns) or 'solo lectura'})"
    return None


def read_denial(project_root: str, path: str) -> str | None:
    """Motivo para bloquear una lectura, o None si está permitida."""
    if not isinstance(path, str) or not path.strip():
        return "ruta vacía"
    rel = relative_inside(project_root, path)
    if rel is None:
        return f"'{path}' está fuera del proyecto"
    seg = _ambiguous_segment(path, rel)
    if seg is not None:
        return f"segmento ambiguo '{seg}'"
    if rel.casefold() in GUARD_SECRET_FILES:
        return f"'{rel}' puede contener credenciales"
    for part in _split(rel):
        low = part.casefold()
        for name in GUARD_SECRET_SEGMENTS:
            if fnmatch.fnmatchcase(low, name):
                return f"'{rel}' puede contener secretos ({name})"
    return None


import json as _json
import sys as _sys

SCOPES = {'sqp-temporal': [], 'sqp-mercados': [], 'sqp-operaciones': [], 'coordinator': []}
EXACT = {'coordinator': ['.superagente/ESTADO.md', '.superagente/proyecto.json']}


def _main() -> int:
    try:
        role = _sys.argv[1]
        data = _json.load(_sys.stdin)
        tool_input = data.get("tool_input") or {}
        path = tool_input.get("file_path") or tool_input.get("notebook_path")
        # Solo CLAUDE_PROJECT_DIR: usar `cwd` desplazaría los patrones si la
        # sesión está en un subdirectorio.
        root = os.environ.get("CLAUDE_PROJECT_DIR")
        if role not in SCOPES:
            reason = f"rol desconocido '{role}'"
        elif not root:
            reason = "no se conoce la raíz del proyecto"
        else:
            reason = write_denial(root, path, SCOPES[role], exact=EXACT.get(role, []))
    except Exception as exc:  # falla cerrado
        reason = f"error del guardián: {exc}"
    if reason:
        # UTF-8 explícito: en Windows la codificación por defecto de un pipe es cp1252.
        _sys.stderr.buffer.write(f"Bloqueado por agent-architect: {reason}\n".encode("utf-8"))
        _sys.stderr.flush()
        return 2
    return 0


if __name__ == "__main__":
    _sys.exit(_main())
