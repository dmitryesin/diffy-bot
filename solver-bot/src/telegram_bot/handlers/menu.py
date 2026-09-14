from __future__ import annotations

from src.logging_config import logger
from src.solver_client import UserSettings
from src.telegram_bot.deps import get_deps
from src.telegram_bot.keyboards import solution_markup
from src.telegram_bot.states import ACTIVE_SOLVE_STATES, ConversationState
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


def reset_solve_progress(context: ContextTypes.DEFAULT_TYPE) -> None:
    keys_to_keep = {"method", "rounding", "language", "hints"}
    for key in list(context.user_data.keys()):
        if key not in keys_to_keep:
            del context.user_data[key]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deps = get_deps(context)

    if update.edited_message:
        return ConversationState.MENU

    user_settings = await deps.solver_client.get_user_settings(
        update.effective_user.id,
        UserSettings(
            method=deps.settings.default_method,
            rounding=deps.settings.default_rounding,
            language=deps.settings.default_language,
            hints=deps.settings.default_hints,
        ),
    )

    context.user_data["method"] = user_settings.get("method", deps.settings.default_method)
    context.user_data["rounding"] = user_settings.get(
        "rounding", deps.settings.default_rounding
    )
    context.user_data["language"] = user_settings.get(
        "language", deps.settings.default_language
    )
    context.user_data["hints"] = user_settings.get("hints", deps.settings.default_hints)

    await deps.solver_client.set_user_settings(
        update.effective_user.id,
        UserSettings(
            method=context.user_data["method"],
            rounding=context.user_data["rounding"],
            language=context.user_data["language"],
            hints=context.user_data["hints"],
        ),
    )

    current_state = context.user_data.get("state")
    current_language = context.user_data.get("language", deps.settings.default_language)

    if current_state in ACTIVE_SOLVE_STATES:
        user = update.message.from_user
        logger.info("User %s canceled solving", user.id)
        reset_solve_progress(context)

    keyboard = [
        [
            InlineKeyboardButton(
                deps.lang_texts[current_language]["solve"], callback_data="solve"
            ),
            InlineKeyboardButton(
                deps.lang_texts[current_language]["settings"], callback_data="settings"
            ),
        ],
        [
            InlineKeyboardButton(
                deps.lang_texts[current_language]["solve_history"],
                callback_data="solve_history",
            )
        ],
    ]

    text_to_send = deps.start_texts.get(current_language, deps.start_texts["en"])

    if update.message:
        await update.message.reply_text(
            text_to_send, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        query = update.callback_query
        await query.answer()
        if query.message and query.message.text:
            await query.edit_message_text(
                text_to_send,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )
        else:
            await query.message.reply_text(
                text_to_send,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )

    return ConversationState.MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deps = get_deps(context)
    current_state = context.user_data.get("state")

    if current_state in ACTIVE_SOLVE_STATES:
        user = update.message.from_user
        logger.info("User %s canceled solving", user.id)

        reset_solve_progress(context)

        current_language = context.user_data.get("language", deps.settings.default_language)

        await update.message.reply_text(
            deps.lang_texts[current_language]["cancel"],
            reply_markup=solution_markup(current_language, deps.lang_texts),
        )
        return ConversationState.MENU
    else:
        if update.message:
            await update.message.delete()
        return current_state
