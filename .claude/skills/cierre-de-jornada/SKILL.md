---
name: cierre-de-jornada
description: Procedimiento de cierre de jornada y sincronización con GitHub. Usar SIEMPRE que el operador escriba «guarda los cambios y cierra sesión» (o «guarda los cambios y cierra la sesión»). Las reglas de seguridad del cierre viven en CLAUDE.md y se aplican igualmente.
---

# Cierre de jornada y sincronización con GitHub

Orden permanente del operador (2026-10-12). Ejecuta este procedimiento completo:

0. Finaliza primero todas las tareas pendientes (orden del operador, 2026-10-17). Lo que dependa de un permiso denegado o de una decisión del operador no bloquea el cierre: se informa en el paso 12 con el comando o la decisión exacta que falta.
1. Guarda todos los archivos y cambios pendientes que estén bajo tu control.
2. Comprueba el estado del repositorio mediante `git status`.
3. Identifica la rama activa y su repositorio remoto.
4. Revisa los cambios realizados durante la sesión.
5. Comprueba que no se incluyan contraseñas, tokens, claves API, archivos `.env` ni otros datos sensibles.
6. Ejecuta las pruebas pertinentes cuando estén disponibles.
7. Prepara exclusivamente los archivos que correspondan al trabajo realizado.
8. Crea un commit con un mensaje descriptivo si existen cambios pendientes.
9. Comprueba si hay cambios remotos nuevos. Si es necesario integrarlos, hazlo de forma segura, sin sobrescribir trabajo ni resolver conflictos arbitrariamente.
10. Ejecuta `git push` hacia la rama remota correspondiente.
11. Verifica que el push se haya completado correctamente y comprueba nuevamente `git status`.
12. Entrega un informe final con la rama, el identificador del commit, el resultado de las pruebas y el estado de sincronización con GitHub.
13. Finaliza la interacción de la sesión.

Encaje con las reglas existentes: este cierre no sustituye a `/memoria-guardar` (obligatorio al cerrar una sesión que cambió código, configuración, datos operativos o decisiones; ver `.claude/CLAUDE.md`) ni a la regla de notas Obsidian de `CLAUDE.md`; cuando apliquen, se hacen antes del paso 7 para que entren en el mismo commit.
