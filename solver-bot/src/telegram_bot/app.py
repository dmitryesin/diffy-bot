from __future__ import annotations

from src.config import Settings, get_settings
from src.i18n import load_language_texts, load_start_texts
from src.solver_client import SolverClient
from src.telegram_bot.deps import BotDeps, store_deps
from src.telegram_bot.handlers import history, menu, settings, solve_flow
from src.telegram_bot.states import ConversationState as State
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)


def build_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("start", menu.start)],
        states={
            State.MENU: [
                CallbackQueryHandler(solve_flow.solve, pattern="^solve$"),
                CallbackQueryHandler(history.solve_history, pattern="^solve_history$"),
                CallbackQueryHandler(history.solve_history, pattern="^solve_history_back$"),
                CallbackQueryHandler(
                    history.solve_history_details, pattern=r"^application_\d+$"
                ),
                CallbackQueryHandler(menu.start, pattern="^back$"),
                CallbackQueryHandler(menu.start, pattern="^menu$"),
                CallbackQueryHandler(settings.settings, pattern="^settings$"),
                CallbackQueryHandler(settings.settings, pattern="^settings_back$"),
                CallbackQueryHandler(settings.settings_method, pattern="^settings_method$"),
                CallbackQueryHandler(
                    settings.settings_rounding, pattern="^settings_rounding$"
                ),
                CallbackQueryHandler(
                    settings.settings_language, pattern="^settings_language$"
                ),
                CallbackQueryHandler(
                    settings.method,
                    pattern="^(euler|midpoint|heun|runge_kutta|dormand_prince)$",
                ),
                CallbackQueryHandler(settings.rounding, pattern="^(4|6|8|16)$"),
                CallbackQueryHandler(settings.language, pattern="^(en|ru|zh)$"),
                CallbackQueryHandler(settings.hints, pattern="^(true|false)$"),
            ],
            State.EQUATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, solve_flow.equation)
            ],
            State.INITIAL_X: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, solve_flow.initial_x)
            ],
            State.INITIAL_Y: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, solve_flow.initial_y)
            ],
            State.REACH_POINT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, solve_flow.reach_point)
            ],
            State.STEP_SIZE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, solve_flow.step_size)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", menu.cancel),
            CommandHandler("start", menu.start),
        ],
    )


def build_application(app_settings: Settings | None = None) -> Application:
    app_settings = app_settings or get_settings()

    solver_client = SolverClient(app_settings)

    async def _on_startup(app: Application) -> None:
        await solver_client.start()

    async def _on_shutdown(app: Application) -> None:
        await solver_client.close()

    application = (
        Application.builder()
        .token(app_settings.telegram_bot_token)
        .post_init(_on_startup)
        .post_shutdown(_on_shutdown)
        .build()
    )

    deps = BotDeps(
        settings=app_settings,
        solver_client=solver_client,
        lang_texts=load_language_texts(),
        start_texts=load_start_texts(),
    )
    store_deps(application.bot_data, deps)

    application.add_handler(build_conversation_handler())
    application.add_handler(CommandHandler("start", menu.start))

    return application


def run() -> None:
    application = build_application()
    application.run_polling(allowed_updates=Update.ALL_TYPES)
