from __future__ import annotations

from src.solver_client import UserSettings
from src.telegram_bot.deps import get_deps
from src.telegram_bot.states import ConversationState
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

NUMERICAL_METHODS = ["euler", "midpoint", "heun", "runge_kutta", "dormand_prince"]
ROUNDING_OPTIONS = ["4", "6", "8"]
NO_ROUNDING_VALUE = "16"
LANGUAGE_OPTIONS = [("en", "English"), ("ru", "Русский"), ("zh", "中文")]


async def _persist_current_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    deps = get_deps(context)
    await deps.solver_client.set_user_settings(
        update.effective_user.id,
        UserSettings(
            method=context.user_data["method"],
            rounding=context.user_data["rounding"],
            language=context.user_data["language"],
            hints=context.user_data["hints"],
        ),
    )


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deps = get_deps(context)
    query = update.callback_query
    await query.answer()

    current_language = context.user_data.get("language", deps.settings.default_language)
    current_hints = context.user_data.get("hints", deps.settings.default_hints)

    keyboard = [
        [
            InlineKeyboardButton(
                deps.lang_texts[current_language]["change_method"],
                callback_data="settings_method",
            )
        ],
        [
            InlineKeyboardButton(
                deps.lang_texts[current_language]["change_rounding"],
                callback_data="settings_rounding",
            )
        ],
        [
            InlineKeyboardButton(
                deps.lang_texts[current_language]["change_language"],
                callback_data="settings_language",
            )
        ],
        [
            InlineKeyboardButton(
                deps.lang_texts[current_language]["hints_switch"]
                + " "
                + deps.lang_texts[current_language]["hints_switch_on"],
                callback_data="true",
            )
            if current_hints == "true"
            else InlineKeyboardButton(
                deps.lang_texts[current_language]["hints_switch"]
                + " "
                + deps.lang_texts[current_language]["hints_switch_off"],
                callback_data="false",
            )
        ],
        [
            InlineKeyboardButton(
                deps.lang_texts[current_language]["back"], callback_data="back"
            )
        ],
    ]

    new_text = deps.lang_texts[current_language]["settings_menu"]
    new_reply_markup = InlineKeyboardMarkup(keyboard)

    if query.message.text != new_text or query.message.reply_markup != new_reply_markup:
        await query.edit_message_text(new_text, reply_markup=new_reply_markup)

    return ConversationState.MENU


async def method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["method"] = query.data
    await _persist_current_settings(update, context)
    await settings_method(update, context)


async def settings_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deps = get_deps(context)
    query = update.callback_query
    await query.answer()

    current_language = context.user_data.get("language", deps.settings.default_language)
    current_method = context.user_data.get("method", deps.settings.default_method)

    numerical_texts = deps.lang_texts[current_language]["numerical_methods"]

    keyboard = []
    for candidate_method in NUMERICAL_METHODS:
        method_name = numerical_texts[candidate_method]
        text = f"→ {method_name} ←" if current_method == candidate_method else method_name
        keyboard.append([InlineKeyboardButton(text, callback_data=candidate_method)])

    keyboard.append(
        [
            InlineKeyboardButton(
                deps.lang_texts[current_language]["back"], callback_data="settings_back"
            )
        ]
    )

    new_text = deps.lang_texts[current_language]["settings_menu"]
    new_reply_markup = InlineKeyboardMarkup(keyboard)

    if query.message.text != new_text or query.message.reply_markup != new_reply_markup:
        await query.edit_message_text(new_text, reply_markup=new_reply_markup)

    return ConversationState.MENU


async def rounding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["rounding"] = query.data
    await _persist_current_settings(update, context)
    await settings_rounding(update, context)


async def settings_rounding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deps = get_deps(context)
    query = update.callback_query
    await query.answer()

    current_language = context.user_data.get("language", deps.settings.default_language)
    current_rounding = context.user_data.get("rounding", deps.settings.default_rounding)

    keyboard = []

    row = []
    for rounding_option in ROUNDING_OPTIONS:
        text = (
            f"→ {rounding_option} ←" if current_rounding == rounding_option else rounding_option
        )
        row.append(InlineKeyboardButton(text, callback_data=rounding_option))
    keyboard.append(row)

    no_rounding_text = deps.lang_texts[current_language]["without_rounding"]
    text = (
        f"→ {no_rounding_text} ←"
        if current_rounding == NO_ROUNDING_VALUE
        else no_rounding_text
    )
    keyboard.append([InlineKeyboardButton(text, callback_data=NO_ROUNDING_VALUE)])

    keyboard.append(
        [
            InlineKeyboardButton(
                deps.lang_texts[current_language]["back"], callback_data="settings_back"
            )
        ]
    )

    new_text = deps.lang_texts[current_language]["settings_menu"]
    new_reply_markup = InlineKeyboardMarkup(keyboard)

    if query.message.text != new_text or query.message.reply_markup != new_reply_markup:
        await query.edit_message_text(new_text, reply_markup=new_reply_markup)

    return ConversationState.MENU


async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["language"] = query.data
    await _persist_current_settings(update, context)
    await settings_language(update, context)


async def settings_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deps = get_deps(context)
    query = update.callback_query
    await query.answer()

    current_language = context.user_data.get("language", deps.settings.default_language)

    keyboard = []
    for language_callback, language_label in LANGUAGE_OPTIONS:
        text = (
            f"→ {language_label} ←"
            if current_language == language_callback
            else language_label
        )
        keyboard.append([InlineKeyboardButton(text, callback_data=language_callback)])

    keyboard.append(
        [
            InlineKeyboardButton(
                deps.lang_texts[current_language]["back"], callback_data="settings_back"
            )
        ]
    )

    new_text = deps.lang_texts[current_language]["settings_menu"]
    new_reply_markup = InlineKeyboardMarkup(keyboard)

    if query.message.text != new_text or query.message.reply_markup != new_reply_markup:
        await query.edit_message_text(new_text, reply_markup=new_reply_markup)

    return ConversationState.MENU


async def hints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deps = get_deps(context)
    query = update.callback_query
    await query.answer()

    current_hints = (
        "false"
        if context.user_data.get("hints", deps.settings.default_hints) == "true"
        else "true"
    )
    context.user_data["hints"] = current_hints
    await _persist_current_settings(update, context)

    return await settings(update, context)
