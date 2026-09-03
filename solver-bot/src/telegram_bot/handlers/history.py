from __future__ import annotations

import json

import telegram
from src.formatting.result_formatter import print_solution
from src.logging_config import logger
from src.plotting.plotter import plot_solution
from src.telegram_bot.deps import get_deps
from src.telegram_bot.states import ConversationState
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.ext import ContextTypes

_BACKEND_METHOD_LABEL_KEYS = {
    "euler": "euler",
    "midpoint": "midpoint",
    "heun": "heun",
    "rungeKutta": "runge_kutta",
    "dormandPrince": "dormand_prince",
}


async def solve_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deps = get_deps(context)
    query = update.callback_query
    await query.answer()

    current_language = context.user_data.get("language", deps.settings.default_language)

    recent_applications = await deps.solver_client.get_recent_applications(
        update.effective_user.id
    )

    keyboard = []

    for index, application in enumerate(recent_applications):
        try:
            parameters = json.loads(application.get("parameters", "{}"))
            equation = parameters.get("userEquation")
        except json.JSONDecodeError:
            equation = ""

        keyboard.append(
            [InlineKeyboardButton(f"{equation}", callback_data=f"application_{index}")]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                deps.lang_texts[current_language]["back"], callback_data="back"
            )
        ]
    )

    if query.message and query.message.text:
        await query.edit_message_text(
            deps.lang_texts[current_language]["solve_history_menu"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await query.message.reply_text(
            deps.lang_texts[current_language]["solve_history_menu"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    return ConversationState.MENU


async def solve_history_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deps = get_deps(context)
    query = update.callback_query
    await query.answer()

    current_language = context.user_data.get("language", deps.settings.default_language)
    current_rounding = context.user_data.get("rounding", deps.settings.default_rounding)

    application_index = int(query.data.split("_")[1])

    recent_applications = await deps.solver_client.get_recent_applications(
        update.effective_user.id
    )

    if application_index >= len(recent_applications):
        await query.edit_message_text(
            deps.lang_texts[current_language]["application_not_found"],
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            deps.lang_texts[current_language]["back"],
                            callback_data="solve_history_back",
                        )
                    ]
                ]
            ),
        )
        return ConversationState.MENU

    application = recent_applications[application_index]
    application_id = application.get("id")
    results = await deps.solver_client.get_results(application_id)

    try:
        parameters = json.loads(application.get("parameters", "{}"))
        order = parameters.get("order", 1)

        method = parameters.get("method", "")
        user_equation = parameters.get("userEquation", "")
        initial_x = parameters.get("initialX", "")
        initial_y = parameters.get("initialY", "")
        reach_point = parameters.get("reachPoint", "")
        step_size = parameters.get("stepSize", "")

        data = json.loads(results[0].get("data", "{}"))
        x_values = data.get("xValues", [])
        y_values = data.get("yValues", [])
        solution = data.get("solution", "")

        plot_graph = plot_solution(x_values, y_values, order)

        initial_y_str = ", ".join([str(y) for y in initial_y]) if isinstance(initial_y, list) else str(initial_y)

        method_label_key = _BACKEND_METHOD_LABEL_KEYS.get(method, method)
        method_display = deps.lang_texts[current_language]["numerical_methods"].get(
            method_label_key, method
        )

        details_text = (
            f"<b>{deps.lang_texts[current_language]['method']}:</b> {method_display}\n"
            f"<b>{deps.lang_texts[current_language]['equation']}:</b> {user_equation}\n"
            f"<b>{deps.lang_texts[current_language]['initial_x']}:</b> {initial_x}\n"
            f"<b>{deps.lang_texts[current_language]['initial_y']}:</b> {initial_y_str}\n"
            f"<b>{deps.lang_texts[current_language]['reach_point']}:</b> {reach_point}\n"
            f"<b>{deps.lang_texts[current_language]['step_size']}:</b> {step_size}\n\n"
            f"<b>{deps.lang_texts[current_language]['solution']}:</b>\n"
            f"{print_solution(solution, order, current_rounding)}"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    deps.lang_texts[current_language]["back"],
                    callback_data="solve_history_back",
                )
            ]
        ]

        media = InputMediaPhoto(media=plot_graph, caption=details_text, parse_mode="HTML")

        try:
            await query.edit_message_media(
                media=media,
                reply_markup=InlineKeyboardMarkup(keyboard),
                write_timeout=60,
                pool_timeout=30,
            )
        except telegram.error.TimedOut:
            logger.warning(
                "Timeout while sending media for user %s, falling back to text only",
                update.effective_user.id,
            )
            await query.edit_message_text(
                details_text, reply_markup=InlineKeyboardMarkup(keyboard)
            )
        finally:
            plot_graph.close()

    except Exception as e:
        logger.error(f"Error displaying application details: {e}")
        await query.edit_message_text(
            deps.lang_texts[current_language]["error_displaying_application"],
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            deps.lang_texts[current_language]["back"],
                            callback_data="solve_history_back",
                        )
                    ]
                ]
            ),
        )

    return ConversationState.MENU
