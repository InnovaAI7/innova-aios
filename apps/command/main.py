"""AI Command Bot — Telegram bot entry point.

Simplified boot sequence:
1. Load config from .env
2. Print boot banner with system checks
3. Clear stale Telegram polling lock
4. Wire up orchestrator, task registry, cost tracker
5. Register router and start polling (with crash recovery)
"""

import asyncio
import logging
import os
import shutil
import subprocess
import signal
import sys
from pathlib import Path

# Remove CLAUDECODE env var so Agent SDK can spawn Claude Code subprocesses.
# When developing inside a Claude Code session this var is set and blocks
# subprocess spawning — popping it here ensures clean agent launches.
os.environ.pop("CLAUDECODE", None)

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .bot import router, set_orchestrator
from .config import load_config
from .cost_tracker import CostTracker
from .logger import (
    setup_logging,
    get_logger,
    print_banner,
    print_separator,
    print_system_checks,
    print_ready,
    SystemCheck,
)
from .orchestrator import Orchestrator


# Maximum size for stdout/stderr logs before trimming (5 MB)
_MAX_LOG_BYTES = 5 * 1024 * 1024


def _trim_launchd_logs() -> None:
    """Trim stdout/stderr log files if they exceed the size limit.

    launchd doesn't support log rotation, so we do it on startup.
    Keeps the last ~50% of the file to preserve recent context.
    """
    workspace = Path(__file__).resolve().parent.parent.parent
    for name in ("command.stdout.log", "command.stderr.log"):
        log_path = workspace / "data" / name
        if not log_path.exists():
            continue
        try:
            size = log_path.stat().st_size
            if size > _MAX_LOG_BYTES:
                content = log_path.read_bytes()
                # Keep the last half
                half = len(content) // 2
                # Find next newline after the midpoint for a clean cut
                cut = content.find(b"\n", half)
                if cut == -1:
                    cut = half
                log_path.write_bytes(content[cut + 1:])
                logging.getLogger("boot").info(
                    "Trimmed %s: %d KB -> %d KB",
                    name, size // 1024, (size - cut) // 1024,
                )
        except OSError:
            pass


async def main() -> None:
    # ── Logging & banner ─────────────────────────────────────────────────
    setup_logging()
    print_banner()

    boot = get_logger("boot")
    system = get_logger("system")

    # ── Trim old logs ────────────────────────────────────────────────────
    _trim_launchd_logs()

    # ── Load configuration ───────────────────────────────────────────────
    boot.info("Loading configuration...")
    config = load_config()

    # On cloud, clear any stale sessions baked into the Docker image.
    # Sessions created locally (OAuth) won't work with the API key on cloud.
    if os.getenv("DIGITALOCEAN_APP"):
        sessions_path = Path(config.workspace_dir) / "data" / "command" / "agent_sessions.json"
        if sessions_path.exists():
            try:
                import json
                data = json.loads(sessions_path.read_text())
                if data:
                    boot.info("Clearing %d stale session(s) from Docker image", len(data))
                    sessions_path.write_text("{}")
            except Exception:
                pass
    config.log_dir.mkdir(parents=True, exist_ok=True)

    boot.info(
        "Model: %s  |  Budget: $%.2f/msg  |  Max turns: %d",
        config.general_agent_model, config.general_agent_max_budget, config.general_agent_max_turns,
    )
    print_separator()

    # ── System checks ────────────────────────────────────────────────────
    checks: list[SystemCheck] = []

    # Config loaded
    checks.append(SystemCheck(
        "Config loaded", True, f"model: {config.general_agent_model}",
    ))

    # Log directory
    checks.append(SystemCheck("Log directory", True, str(config.log_dir)))

    # ── Initialize bot ───────────────────────────────────────────────────
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Clear any stale Telegram polling lock (fixes TelegramConflictError).
    # deleteWebhook clears webhooks; getUpdates with offset=-1 flushes stale polls.
    boot.info("Clearing Telegram polling lock...")
    try:
        await bot.delete_webhook(drop_pending_updates=False)
    except Exception:
        pass
    # Flush any stale getUpdates long-poll by claiming the session briefly
    for attempt in range(5):
        try:
            await bot.get_updates(offset=-1, timeout=1)
            break
        except Exception:
            boot.info("Waiting for polling lock to release... (%d/5)", attempt + 1)
            await asyncio.sleep(3)

    # Verify Claude Code CLI is available and working
    cli_path = shutil.which("claude")
    if cli_path:
        try:
            cli_env = {**os.environ, "CLAUDECODE": ""}
            result = subprocess.run(
                [cli_path, "--version"],
                capture_output=True, text=True, timeout=15,
                env=cli_env,
            )
            version = result.stdout.strip() or result.stderr.strip()
            checks.append(SystemCheck("Claude CLI", True, f"{cli_path} — {version[:40]}"))
        except Exception as e:
            checks.append(SystemCheck("Claude CLI", False, f"found at {cli_path} but failed: {e}"))

        # On cloud, do a quick smoke test to verify the API key works with the CLI
        if os.getenv("DIGITALOCEAN_APP") and os.getenv("ANTHROPIC_API_KEY"):
            try:
                smoke = subprocess.run(
                    [cli_path, "-p", "respond with just OK", "--max-turns", "1",
                     "--output-format", "text", "--model", "haiku"],
                    capture_output=True, text=True, timeout=30,
                    env=cli_env,
                )
                if smoke.returncode == 0:
                    checks.append(SystemCheck("CLI smoke test", True, "API key + CLI working"))
                else:
                    stderr_preview = (smoke.stderr or "no stderr")[:120]
                    checks.append(SystemCheck(
                        "CLI smoke test", False,
                        f"exit code {smoke.returncode}: {stderr_preview}",
                    ))
            except subprocess.TimeoutExpired:
                checks.append(SystemCheck("CLI smoke test", False, "timed out after 30s"))
            except Exception as e:
                checks.append(SystemCheck("CLI smoke test", False, str(e)[:80]))
    else:
        checks.append(SystemCheck("Claude CLI", False, "not found in PATH"))

    # Check API key availability on cloud
    if os.getenv("DIGITALOCEAN_APP"):
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        has_key = bool(api_key)
        if has_key:
            # Validate the key format (should start with sk-ant-)
            key_preview = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else "***"
            key_valid = api_key.startswith("sk-ant-")
            checks.append(SystemCheck(
                "API Key (cloud)", key_valid,
                f"ANTHROPIC_API_KEY set ({key_preview})"
                if key_valid else f"ANTHROPIC_API_KEY set but unexpected format ({key_preview})",
            ))
        else:
            checks.append(SystemCheck(
                "API Key (cloud)", False,
                "ANTHROPIC_API_KEY missing — CLI will fail",
            ))

    # Verify Telegram connection
    try:
        me = await bot.get_me()
        checks.append(SystemCheck("Telegram", True, f"@{me.username}"))
    except Exception as e:
        checks.append(SystemCheck("Telegram", False, str(e)[:60]))

    print_system_checks(checks)
    print_separator()

    # Check for failures
    failed = [c for c in checks if not c.passed]
    if failed:
        boot.warning("Some checks failed — bot will start anyway")

    # ── Wire up components ───────────────────────────────────────────────
    cost_tracker = CostTracker(config.log_dir)
    orchestrator = Orchestrator(bot, config, cost_tracker)
    set_orchestrator(orchestrator, config)

    dp = Dispatcher()
    dp.include_router(router)

    @dp.startup()
    async def on_startup() -> None:
        print_ready()
        # Build startup message with check results for Telegram
        lines = ["Command Bot is online."]
        for c in checks:
            icon = "\u2705" if c.passed else "\u274c"
            lines.append(f"{icon} {c.name}: {c.detail}")
        try:
            await bot.send_message(
                chat_id=config.group_id,
                text="\n".join(lines),
            )
        except Exception:
            system.warning("Could not send startup message to Telegram")

    @dp.shutdown()
    async def on_shutdown() -> None:
        system.info("Shutting down...")

    # ── Start polling with crash recovery ────────────────────────────────
    # If polling crashes (e.g. sustained DNS failure), wait and retry
    # instead of letting the process die. launchd will restart us, but
    # that creates log noise and loses the warm bot/dispatcher state.
    max_retries = 10
    retry_delay = 10  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            await dp.start_polling(bot)
            break  # Clean shutdown (SIGTERM/SIGINT) — exit normally
        except (KeyboardInterrupt, SystemExit):
            system.info("Received shutdown signal")
            break
        except Exception as e:
            system.error(
                "Polling crashed (attempt %d/%d): %s: %s",
                attempt, max_retries, type(e).__name__, e,
            )
            if attempt < max_retries:
                system.info("Restarting polling in %ds...", retry_delay)
                await asyncio.sleep(retry_delay)
                # Exponential backoff capped at 60s
                retry_delay = min(retry_delay * 2, 60)
            else:
                system.error("Max retries reached — exiting")
                sys.exit(1)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
