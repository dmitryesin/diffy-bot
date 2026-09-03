from __future__ import annotations

import asyncio
import json

import telegram
from src.equation.parser import format_equation
from src.equation.validator import validate_parentheses, validate_symbols
from src.formatting.result_formatter import print_solution
from src.logging_config import logger
from src.plotting.plotter import plot_solution
from src.solver_client import SolveParameters
from src.telegram_bot.deps import BotDeps, get_deps
from src.telegram_bot.handlers.menu import reset_solve_progress
from src.telegram_bot.keyboards import solution_markup
from src.telegram_bot.states import ConversationState
from telegram import InputMediaPhoto, Update
from telegram.ext import ContextTypes


async def send_localized_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, key: str
) -> None:
    deps = get_deps(context)
    current_language = context.user_data.get("language", deps.settings.default_language)
    current_hints = context.user_data.get("hints", deps.settings.default_hints)

    text = deps.lang_texts[current_language].get(key, "")

    if current_hints == "true":
        text += f"<i>\n\n{deps.lang_texts[current_language]['hints_text']}</i>"
        text += f"<i> {deps.lang_texts[current_language]['hints'].get(key, '')}</i>"

    if update.message:
        await update.message.reply_text(text, parse_mode="HTML")
    else:
        query = update.callback_query
        await query.answer()
        if query.message and query.message.text:
            await query.edit_message_text(text, parse_mode="HTML")
        else:
            await query.message.reply_text(text, parse_mode="HTML")


async def solve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deps = get_deps(context)
    query = update.callback_query
    await query.answer()

    user = query.from_user

    current_method = context.user_data.get("method", deps.settings.default_method)
    current_rounding = context.user_data.get("rounding", deps.settings.default_rounding)

    logger.info("User %s started solving", user.id)
    logger.info("Method of %s: %s", user.id, current_method)
    logger.info("Rounding of %s: %s", user.id, current_rounding)

    context.user_data["state"] = ConversationState.EQUATION

    await send_localized_message(update, context, "enter_equation")

    return ConversationState.EQUATION


async def equation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deps = get_deps(context)

    if update.edited_message:
        return ConversationState.EQUATION

    user = update.message.from_user
    logger.info("Equation of %s: %s", user.id, update.message.text)

    context.user_data["user_equation"] = update.message.text

    current_language = context.user_data.get("language", deps.settings.default_language)

    is_valid_symbols, error_message = validate_symbols(update.message.text)
    if not is_valid_symbols:
        logger.info("User %s used unsupported symbol: %s", user.id, error_message)
        await update.message.reply_text(
            deps.lang_texts[current_language]["symbols_error"]
            + f"{error_message}. "
            + deps.lang_texts[current_language]["try_again"],
        )
        return ConversationState.EQUATION

    if not validate_parentheses(update.message.text):
        logger.info("User %s used incorrect parentheses", user.id)
        await update.message.reply_text(
            deps.lang_texts[current_language]["parentheses_error"]
            + " "
            + deps.lang_texts[current_language]["try_again"]
        )
        return ConversationState.EQUATION

    formatted_equation, order = format_equation(update.message.text)

    if formatted_equation is None or order is None or order == 0:
        logger.info("User %s used unsupported symbols", user.id)
        await update.message.reply_text(
            deps.lang_texts[current_language]["equation_error"]
            + " "
            + deps.lang_texts[current_language]["try_again"]
        )
        return ConversationState.EQUATION

    logger.info("Formatted Equation of %s: %s", user.id, formatted_equation)
    logger.info("Order of %s: %s", user.id, order)

    context.user_data["formatted_equation"] = formatted_equation
    context.user_data["order"] = order
    context.user_data["state"] = ConversationState.INITIAL_X

    await send_localized_message(update, context, "enter_x")

    return ConversationState.INITIAL_X


async def initial_x(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.edited_message:
        return ConversationState.INITIAL_X

    deps = get_deps(context)
    user = update.message.from_user
    user_input = update.message.text.strip()

    current_language = context.user_data.get("language", deps.settings.default_language)

    try:
        float(user_input)
    except ValueError:
        logger.info("Invalid initial x input by %s: %s", user.id, user_input)
        await update.message.reply_text(
            deps.lang_texts[current_language]["invalid_initial_x"]
            + " "
            + deps.lang_texts[current_language]["try_again"]
        )
        return ConversationState.INITIAL_X

    logger.info("Initial x of %s: %s", user.id, user_input)

    context.user_data["initial_x"] = user_input
    context.user_data["state"] = ConversationState.INITIAL_Y

    if int(context.user_data["order"]) == 1:
        await send_localized_message(update, context, "enter_y")
        return ConversationState.INITIAL_Y
    else:
        await send_localized_message(update, context, "enter_y_multiple")

    return ConversationState.INITIAL_Y


async def initial_y(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.edited_message:
        return ConversationState.INITIAL_Y

    deps = get_deps(context)
    user = update.message.from_user
    user_input = update.message.text.strip()

    splitted_user_input = user_input.split(",") if "," in user_input else user_input.split()

    order = int(context.user_data["order"])

    current_language = context.user_data.get("language", deps.settings.default_language)

    try:
        [float(value) for value in splitted_user_input]
    except ValueError:
        invalid_value = next(
            (
                value
                for value in splitted_user_input
                if not value.replace(".", "", 1).replace("-", "", 1).isdigit()
            ),
            None,
        )
        logger.info("Invalid initial y input by %s: %s", user.id, user_input)
        await update.message.reply_text(
            deps.lang_texts[current_language]["invalid_initial_y"]
            + f"{invalid_value}. "
            + deps.lang_texts[current_language]["try_again"],
        )
        return ConversationState.INITIAL_Y

    if len(splitted_user_input) != order:
        logger.info("Invalid number of initial y values by %s: %s", user.id, user_input)
        await update.message.reply_text(
            deps.lang_texts[current_language]["invalid_initial_y_count1"]
            + f"{len(splitted_user_input)}. "
            + deps.lang_texts[current_language]["invalid_initial_y_count2"]
            + f"{order}. "
            + deps.lang_texts[current_language]["try_again"],
        )
        return ConversationState.INITIAL_Y

    logger.info("Initial y of %s: %s", user.id, user_input)
    context.user_data["initial_y"] = splitted_user_input
    context.user_data["state"] = ConversationState.REACH_POINT

    await send_localized_message(update, context, "enter_reach_point")

    return ConversationState.REACH_POINT


async def reach_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.edited_message:
        return ConversationState.REACH_POINT

    deps = get_deps(context)
    user = update.message.from_user
    user_input = update.message.text.strip()

    current_language = context.user_data.get("language", deps.settings.default_language)

    try:
        reach_point_value = float(user_input)
    except ValueError:
        logger.info("Invalid reach point input by %s: %s", user.id, user_input)
        await update.message.reply_text(
            deps.lang_texts[current_language]["invalid_reach_point"]
            + " "
            + deps.lang_texts[current_language]["try_again"]
        )
        return ConversationState.REACH_POINT

    try:
        initial_x_value = float(context.user_data["initial_x"])
        if abs(reach_point_value - initial_x_value) < 1e-10:
            logger.info("Reach point equals initial x for %s: %s", user.id, user_input)
            await update.message.reply_text(
                deps.lang_texts[current_language]["reach_point_equals_initial"]
                + " "
                + deps.lang_texts[current_language]["try_again"]
            )
            return ConversationState.REACH_POINT
    except Exception as e:
        logger.error(
            "Error comparing reach point with initial x for %s: %s", user.id, e
        )

    logger.info("Reach point of %s: %s", user.id, user_input)
    context.user_data["reach_point"] = user_input
    context.user_data["state"] = ConversationState.STEP_SIZE

    await send_localized_message(update, context, "enter_step_size")

    return ConversationState.STEP_SIZE


async def step_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deps = get_deps(context)
    user = update.message.from_user
    user_input = update.message.text.strip()

    current_language = context.user_data.get("language", deps.settings.default_language)

    try:
        step_value = float(user_input)
    except ValueError:
        logger.info("Invalid step size input by %s: %s", user.id, user_input)
        await update.message.reply_text(
            deps.lang_texts[current_language]["invalid_step_size"]
            + " "
            + deps.lang_texts[current_language]["try_again"]
        )
        return ConversationState.STEP_SIZE

    try:
        initial_x_value = float(context.user_data["initial_x"])
        reach_point_value = float(context.user_data["reach_point"])
        num_points = abs(reach_point_value - initial_x_value) / step_value

        if num_points > deps.settings.max_calculation_points:
            logger.info(
                "Too many calculation points for %s: %d", user.id, int(num_points)
            )
            await update.message.reply_text(
                deps.lang_texts[current_language]["too_many_points"]
                + f"{int(num_points)}. "
                + deps.lang_texts[current_language]["max_points_allowed"]
                + f"{deps.settings.max_calculation_points}. "
                + deps.lang_texts[current_language]["try_again"]
            )
            return ConversationState.STEP_SIZE

    except Exception as e:
        logger.error("Error calculating number of points for %s: %s", user.id, e)

    logger.info("Step size of %s: %s", user.id, user_input)
    context.user_data["step_size"] = user_input

    return await solution(update, context)


async def solution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deps = get_deps(context)

    if update.edited_message:
        return ConversationState.STEP_SIZE

    user = update.message.from_user
    current_language = context.user_data.get("language", deps.settings.default_language)

    processing_message = await update.message.reply_text("⏳")

    try:
        application_id = await deps.solver_client.set_parameters(
            SolveParameters(
                user_id=user.id,
                method=context.user_data["method"],
                order=context.user_data["order"],
                user_equation=context.user_data["user_equation"],
                formatted_equation=context.user_data["formatted_equation"],
                initial_x=context.user_data["initial_x"],
                initial_y=context.user_data["initial_y"],
                reach_point=context.user_data["reach_point"],
                step_size=context.user_data["step_size"],
            )
        )
    except Exception as e:
        logger.error("Error while setting parameters: %s", e)
        reset_solve_progress(context)
        await processing_message.edit_text(
            deps.lang_texts[current_language]["server_error"]
            + " "
            + deps.lang_texts[current_language]["try_again"],
            reply_markup=solution_markup(current_language, deps.lang_texts),
        )
        return ConversationState.MENU

    asyncio.create_task(
        solution_completion_handle(
            application_id, deps, context, processing_message, current_language
        )
    )

    return ConversationState.MENU


async def solution_completion_handle(
    application_id, deps: BotDeps, context: ContextTypes.DEFAULT_TYPE, message, lang: str
) -> None:
    try:
        is_completed = await deps.solver_client.wait_for_application_completion(
            application_id
        )

        if not is_completed:
            await message.edit_text(
                deps.lang_texts[lang]["processing_error"]
                + " "
                + deps.lang_texts[lang]["try_again"],
                reply_markup=solution_markup(lang, deps.lang_texts),
            )
            return

        results = await deps.solver_client.get_results(application_id)

        if not results:
            await message.edit_text(
                deps.lang_texts[lang]["data_error"] + " " + deps.lang_texts[lang]["try_again"],
                reply_markup=solution_markup(lang, deps.lang_texts),
            )
            return

        data = json.loads(results[0].get("data", "{}"))

        x_values = data.get("xValues", [])
        y_values = data.get("yValues", [])
        solution_value = data.get("solution", "")

        if not solution_value or not x_values or not y_values:
            await message.edit_text(
                deps.lang_texts[lang]["data_error"] + " " + deps.lang_texts[lang]["try_again"],
                reply_markup=solution_markup(lang, deps.lang_texts),
            )
            return

        plot_graph = plot_solution(x_values, y_values, context.user_data["order"])
        print_result = print_solution(
            solution_value, context.user_data["order"], context.user_data["rounding"]
        )

        try:
            await message.edit_media(
                media=InputMediaPhoto(plot_graph, caption=print_result),
                reply_markup=solution_markup(lang, deps.lang_texts),
                write_timeout=60,
                pool_timeout=30,
            )
        except telegram.error.TimedOut:
            await message.edit_text(
                print_result, reply_markup=solution_markup(lang, deps.lang_texts)
            )
        finally:
            plot_graph.close()

        reset_solve_progress(context)

    except Exception as e:
        logger.error("Unexpected error in background completion task: %s", e)
        await message.edit_text(
            deps.lang_texts[lang]["server_error"] + " " + deps.lang_texts[lang]["try_again"],
            reply_markup=solution_markup(lang, deps.lang_texts),
        )
