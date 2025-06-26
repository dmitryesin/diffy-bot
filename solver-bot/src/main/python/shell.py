import asyncio
import json
import os
from pathlib import Path

import telegram
from equation.equation_parser import format_equation
from equation.equation_validator import validate_parentheses, validate_symbols
from logger import logger
from plotting.plotter import plot_solution
from printing.printer import print_solution
from spring_client import (
    get_recent_applications,
    get_results,
    get_user_settings,
    set_parameters,
    set_user_settings,
    wait_for_application_completion,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

PY_DIR = Path(__file__).parent

languages_path = PY_DIR / "languages.json"

with open(languages_path, "r", encoding="utf-8") as f:
    LANG_TEXTS = json.load(f)

MENU, EQUATION, INITIAL_X, INITIAL_Y, REACH_POINT, STEP_SIZE = range(6)

DEFAULT_METHOD = "runge_kutta"
DEFAULT_ROUNDING = "4"
DEFAULT_LANGUAGE = "en"
DEFAULT_HINTS = "true"

MAX_CALCULATION_POINTS = 100000


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.edited_message:
        return MENU

    user_settings = await get_user_settings(
        update.effective_user.id,
        DEFAULT_METHOD,
        DEFAULT_ROUNDING,
        DEFAULT_LANGUAGE,
        DEFAULT_HINTS,
    )

    context.user_data["method"] = user_settings.get("method", DEFAULT_METHOD)
    context.user_data["rounding"] = user_settings.get("rounding", DEFAULT_ROUNDING)
    context.user_data["language"] = user_settings.get("language", DEFAULT_LANGUAGE)
    context.user_data["hints"] = user_settings.get("hints", DEFAULT_HINTS)

    await set_user_settings(
        update.effective_user.id,
        context.user_data["method"],
        context.user_data["rounding"],
        context.user_data["language"],
        context.user_data["hints"],
    )

    current_state = context.user_data.get("state", None)
    current_language = context.user_data.get("language", DEFAULT_LANGUAGE)

    if current_state in [EQUATION, INITIAL_X, INITIAL_Y, REACH_POINT, STEP_SIZE]:
        user = update.message.from_user
        logger.info("User %s canceled solving", user.id)

        await save_user_settings(context)

    keyboard = [
        [
            InlineKeyboardButton(
                LANG_TEXTS[current_language]["solve"], callback_data="solve"
            ),
            InlineKeyboardButton(
                LANG_TEXTS[current_language]["settings"], callback_data="settings"
            ),
        ],
        [
            InlineKeyboardButton(
                LANG_TEXTS[current_language]["solve_history"],
                callback_data="solve_history",
            )
        ],
    ]

    texts = {}
    for lang_code in ["en", "ru", "zh"]:
        file_path = PY_DIR / "assets" / "texts" / f"START_{lang_code.upper()}.txt"
        with open(file_path, "r", encoding="utf-8") as file:
            texts[lang_code] = file.read()

    text_to_send = texts.get(current_language, texts["en"])

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

    return MENU


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    current_language = context.user_data.get("language", DEFAULT_LANGUAGE)
    current_hints = context.user_data.get("hints", DEFAULT_HINTS)

    keyboard = [
        [
            InlineKeyboardButton(
                LANG_TEXTS[current_language]["change_method"],
                callback_data="settings_method",
            )
        ],
        [
            InlineKeyboardButton(
                LANG_TEXTS[current_language]["change_rounding"],
                callback_data="settings_rounding",
            )
        ],
        [
            InlineKeyboardButton(
                LANG_TEXTS[current_language]["change_language"],
                callback_data="settings_language",
            )
        ],
        [
            InlineKeyboardButton(
                LANG_TEXTS[current_language]["hints_switch"]
                + " "
                + LANG_TEXTS[current_language]["hints_switch_on"],
                callback_data="true",
            )
            if current_hints == "true"
            else InlineKeyboardButton(
                LANG_TEXTS[current_language]["hints_switch"]
                + " "
                + LANG_TEXTS[current_language]["hints_switch_off"],
                callback_data="false",
            )
        ],
        [
            InlineKeyboardButton(
                LANG_TEXTS[current_language]["back"], callback_data="back"
            )
        ],
    ]

    new_text = LANG_TEXTS[current_language]["settings_menu"]
    new_reply_markup = InlineKeyboardMarkup(keyboard)

    if query.message.text != new_text or query.message.reply_markup != new_reply_markup:
        await query.edit_message_text(new_text, reply_markup=new_reply_markup)

    return MENU


async def method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    current_method = query.data
    context.user_data["method"] = current_method

    await set_user_settings(
        update.effective_user.id,
        context.user_data["method"],
        context.user_data["rounding"],
        context.user_data["language"],
        context.user_data["hints"],
    )

    await settings_method(update, context)


async def settings_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    current_language = context.user_data.get("language", DEFAULT_LANGUAGE)
    current_method = context.user_data.get("method", DEFAULT_METHOD)

    methods = ["euler", "midpoint", "heun", "runge_kutta", "dormand_prince"]

    numerical_texts = LANG_TEXTS[current_language]["numerical_methods"]

    keyboard = []

    for method in methods:
        method_name = numerical_texts[method]
        text = f"→ {method_name} ←" if current_method == method else method_name
        keyboard.append([InlineKeyboardButton(text, callback_data=method)])

    keyboard.append(
        [
            InlineKeyboardButton(
                LANG_TEXTS[current_language]["back"], callback_data="settings_back"
            )
        ]
    )

    new_text = LANG_TEXTS[current_language]["settings_menu"]
    new_reply_markup = InlineKeyboardMarkup(keyboard)

    if query.message.text != new_text or query.message.reply_markup != new_reply_markup:
        await query.edit_message_text(new_text, reply_markup=new_reply_markup)

    return MENU


async def rounding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    current_rounding = query.data
    context.user_data["rounding"] = current_rounding

    await set_user_settings(
        update.effective_user.id,
        context.user_data["method"],
        context.user_data["rounding"],
        context.user_data["language"],
        context.user_data["hints"],
    )

    await settings_rounding(update, context)


async def settings_rounding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    current_language = context.user_data.get("language", DEFAULT_LANGUAGE)
    current_rounding = context.user_data.get("rounding", DEFAULT_ROUNDING)

    roundings = ["4", "6", "8"]

    keyboard = []

    row = []
    for rounding in roundings:
        text = f"→ {rounding} ←" if current_rounding == rounding else rounding
        row.append(InlineKeyboardButton(text, callback_data=rounding))
    keyboard.append(row)

    no_rounding_text = LANG_TEXTS[current_language]["without_rounding"]
    text = f"→ {no_rounding_text} ←" if current_rounding == "16" else no_rounding_text
    keyboard.append([InlineKeyboardButton(text, callback_data="16")])

    keyboard.append(
        [
            InlineKeyboardButton(
                LANG_TEXTS[current_language]["back"], callback_data="settings_back"
            )
        ]
    )

    new_text = LANG_TEXTS[current_language]["settings_menu"]
    new_reply_markup = InlineKeyboardMarkup(keyboard)

    if query.message.text != new_text or query.message.reply_markup != new_reply_markup:
        await query.edit_message_text(new_text, reply_markup=new_reply_markup)

    return MENU


async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    current_language = query.data
    context.user_data["language"] = current_language

    await set_user_settings(
        update.effective_user.id,
        context.user_data["method"],
        context.user_data["rounding"],
        context.user_data["language"],
        context.user_data["hints"],
    )

    await settings_language(update, context)


async def settings_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    current_language = context.user_data.get("language", DEFAULT_LANGUAGE)

    languages = [("en", "English"), ("ru", "Русский"), ("zh", "中文")]

    keyboard = []

    for language_callback, language in languages:
        text = f"→ {language} ←" if current_language == language_callback else language
        keyboard.append([InlineKeyboardButton(text, callback_data=language_callback)])

    keyboard.append(
        [
            InlineKeyboardButton(
                LANG_TEXTS[current_language]["back"], callback_data="settings_back"
            )
        ]
    )

    new_text = LANG_TEXTS[current_language]["settings_menu"]
    new_reply_markup = InlineKeyboardMarkup(keyboard)

    if query.message.text != new_text or query.message.reply_markup != new_reply_markup:
        await query.edit_message_text(new_text, reply_markup=new_reply_markup)

    return MENU


async def hints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    current_hints = (
        "false" if context.user_data.get("hints", DEFAULT_HINTS) == "true" else "true"
    )
    context.user_data["hints"] = current_hints

    await set_user_settings(
        update.effective_user.id,
        context.user_data["method"],
        context.user_data["rounding"],
        context.user_data["language"],
        context.user_data["hints"],
    )

    return await settings(update, context)


async def solve_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    current_language = context.user_data.get("language", DEFAULT_LANGUAGE)

    recent_applications = await get_recent_applications(update.effective_user.id)

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
                LANG_TEXTS[current_language]["back"], callback_data="back"
            )
        ]
    )

    if query.message and query.message.text:
        await query.edit_message_text(
            LANG_TEXTS[current_language]["solve_history_menu"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await query.message.reply_text(
            LANG_TEXTS[current_language]["solve_history_menu"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    return MENU


async def solve_history_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    current_language = context.user_data.get("language", DEFAULT_LANGUAGE)
    current_rounding = context.user_data.get("rounding", DEFAULT_ROUNDING)

    application_index = int(query.data.split("_")[1])

    recent_applications = await get_recent_applications(update.effective_user.id)

    if application_index >= len(recent_applications):
        await query.edit_message_text(
            LANG_TEXTS[current_language]["application_not_found"],
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            LANG_TEXTS[current_language]["back"],
                            callback_data="solve_history_back",
                        )
                    ]
                ]
            ),
        )
        return MENU

    application = recent_applications[application_index]
    application_id = application.get("id")
    results = await get_results(application_id)

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
        x_values = data.get("xvalues", [])
        y_values = data.get("yvalues", [])
        solution = data.get("solution", "")

        plot_graph = plot_solution(x_values, y_values, order)

        if isinstance(initial_y, list):
            initial_y_str = ", ".join([str(y) for y in initial_y])
        else:
            initial_y_str = str(initial_y)

        method_mapping = {
            "euler": LANG_TEXTS[current_language]["numerical_methods"]["euler"],
            "midpoint": LANG_TEXTS[current_language]["numerical_methods"]["midpoint"],
            "heun": LANG_TEXTS[current_language]["numerical_methods"]["heun"],
            "rungeKutta": LANG_TEXTS[current_language]["numerical_methods"][
                "runge_kutta"
            ],
            "dormandPrince": LANG_TEXTS[current_language]["numerical_methods"][
                "dormand_prince"
            ],
        }

        method_display = method_mapping.get(method, method)

        details_text = (
            f"<b>{LANG_TEXTS[current_language]['method']}:</b> {method_display}\n"
            f"<b>{LANG_TEXTS[current_language]['equation']}:</b> {user_equation}\n"
            f"<b>{LANG_TEXTS[current_language]['initial_x']}:</b> {initial_x}\n"
            f"<b>{LANG_TEXTS[current_language]['initial_y']}:</b> {initial_y_str}\n"
            f"<b>{LANG_TEXTS[current_language]['reach_point']}:</b> {reach_point}\n"
            f"<b>{LANG_TEXTS[current_language]['step_size']}:</b> {step_size}\n\n"
            f"<b>{LANG_TEXTS[current_language]['solution']}:</b>\n"
            f"{print_solution(solution, order, current_rounding)}"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    LANG_TEXTS[current_language]["back"],
                    callback_data="solve_history_back",
                )
            ]
        ]

        media = InputMediaPhoto(
            media=plot_graph, caption=details_text, parse_mode="HTML"
        )

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
            LANG_TEXTS[current_language]["error_displaying_application"],
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            LANG_TEXTS[current_language]["back"],
                            callback_data="solve_history_back",
                        )
                    ]
                ]
            ),
        )

    return MENU


async def send_localized_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, key_without_hint, key_with_hint
):
    current_language = context.user_data.get("language", DEFAULT_LANGUAGE)
    current_hints = context.user_data.get("hints", DEFAULT_HINTS)

    text = LANG_TEXTS[current_language].get(key_without_hint, "")

    if current_hints == "true":
        text += f"<i>\n\n{LANG_TEXTS[current_language]['hints_text']}</i>"
        text += f"<i> {LANG_TEXTS[current_language].get(key_with_hint, '')}</i>"

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
    query = update.callback_query
    await query.answer()

    user = query.from_user

    current_method = context.user_data.get("method", DEFAULT_METHOD)
    current_rounding = context.user_data.get("rounding", DEFAULT_ROUNDING)

    logger.info("User %s started solving", user.id)
    logger.info("Method of %s: %s", user.id, current_method)
    logger.info("Rounding of %s: %s", user.id, current_rounding)

    context.user_data["state"] = EQUATION

    await send_localized_message(
        update, context, "enter_equation", "hints_enter_equation"
    )

    return EQUATION


async def equation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.edited_message:
        return EQUATION

    user = update.message.from_user
    logger.info("Equation of %s: %s", user.id, update.message.text)

    context.user_data["user_equation"] = update.message.text

    current_language = context.user_data.get("language", DEFAULT_LANGUAGE)

    is_valid_symbols, error_message = validate_symbols(update.message.text)
    if not is_valid_symbols:
        logger.info("User %s used unsupported symbol: %s", user.id, error_message)
        await update.message.reply_text(
            LANG_TEXTS[current_language]["symbols_error"]
            + f"{error_message}. "
            + LANG_TEXTS[current_language]["try_again"],
        )
        return EQUATION

    if not validate_parentheses(update.message.text):
        logger.info("User %s used incorrect parentheses", user.id)
        await update.message.reply_text(
            LANG_TEXTS[current_language]["parentheses_error"]
            + " "
            + LANG_TEXTS[current_language]["try_again"]
        )
        return EQUATION

    formatted_equation, order = format_equation(update.message.text)

    if formatted_equation is None or order is None or order == 0:
        logger.info("User %s used unsupported symbols", user.id)
        await update.message.reply_text(
            LANG_TEXTS[current_language]["equation_error"]
            + " "
            + LANG_TEXTS[current_language]["try_again"]
        )
        return EQUATION

    logger.info("Formatted Equation of %s: %s", user.id, formatted_equation)
    logger.info("Order of %s: %s", user.id, order)

    context.user_data["formatted_equation"] = formatted_equation
    context.user_data["order"] = order
    context.user_data["state"] = INITIAL_X

    await send_localized_message(update, context, "enter_x", "hints_enter_x")

    return INITIAL_X


async def initial_x(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.edited_message:
        return INITIAL_X

    user = update.message.from_user
    user_input = update.message.text.strip()

    current_language = context.user_data.get("language", DEFAULT_LANGUAGE)

    try:
        float(user_input)
    except ValueError:
        logger.info("Invalid initial x input by %s: %s", user.id, user_input)
        await update.message.reply_text(
            LANG_TEXTS[current_language]["invalid_initial_x"]
            + " "
            + LANG_TEXTS[current_language]["try_again"]
        )
        return INITIAL_X

    logger.info("Initial x of %s: %s", user.id, user_input)

    context.user_data["initial_x"] = user_input
    context.user_data["state"] = INITIAL_Y

    if int(context.user_data["order"]) == 1:
        await send_localized_message(update, context, "enter_y", "hints_enter_y")
        return INITIAL_Y
    else:
        await send_localized_message(
            update, context, "enter_y_multiple", "hints_enter_y_multiple"
        )

    return INITIAL_Y


async def initial_y(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.edited_message:
        return INITIAL_Y

    user = update.message.from_user
    user_input = update.message.text.strip()

    if "," in user_input:
        splitted_user_input = user_input.split(",")
    else:
        splitted_user_input = user_input.split()

    order = int(context.user_data["order"])

    current_language = context.user_data.get("language", DEFAULT_LANGUAGE)

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
            LANG_TEXTS[current_language]["invalid_initial_y"]
            + f"{invalid_value}. "
            + LANG_TEXTS[current_language]["try_again"],
        )
        return INITIAL_Y

    if len(splitted_user_input) != order:
        logger.info("Invalid number of initial y values by %s: %s", user.id, user_input)
        await update.message.reply_text(
            LANG_TEXTS[current_language]["invalid_initial_y_count1"]
            + f"{len(splitted_user_input)}. "
            + LANG_TEXTS[current_language]["invalid_initial_y_count2"]
            + f"{order}. "
            + LANG_TEXTS[current_language]["try_again"],
        )
        return INITIAL_Y

    logger.info("Initial y of %s: %s", user.id, user_input)
    context.user_data["initial_y"] = splitted_user_input
    context.user_data["state"] = REACH_POINT

    await send_localized_message(
        update, context, "enter_reach_point", "hints_enter_reach_point"
    )

    return REACH_POINT


async def reach_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.edited_message:
        return REACH_POINT

    user = update.message.from_user
    user_input = update.message.text.strip()

    current_language = context.user_data.get("language", DEFAULT_LANGUAGE)

    try:
        reach_point_value = float(user_input)
    except ValueError:
        logger.info("Invalid reach point input by %s: %s", user.id, user_input)
        await update.message.reply_text(
            LANG_TEXTS[current_language]["invalid_reach_point"]
            + " "
            + LANG_TEXTS[current_language]["try_again"]
        )
        return REACH_POINT

    try:
        initial_x_value = float(context.user_data["initial_x"])
        if abs(reach_point_value - initial_x_value) < 1e-10:
            logger.info("Reach point equals initial x for %s: %s", user.id, user_input)
            await update.message.reply_text(
                LANG_TEXTS[current_language]["reach_point_equals_initial"]
                + " "
                + LANG_TEXTS[current_language]["try_again"]
            )
            return REACH_POINT
    except Exception as e:
        logger.error(
            "Error comparing reach point with initial x for %s: %s", user.id, e
        )

    logger.info("Reach point of %s: %s", user.id, user_input)
    context.user_data["reach_point"] = user_input
    context.user_data["state"] = STEP_SIZE

    await send_localized_message(
        update, context, "enter_step_size", "hints_enter_step_size"
    )

    return STEP_SIZE


async def step_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_input = update.message.text.strip()

    current_language = context.user_data.get("language", DEFAULT_LANGUAGE)

    try:
        step_value = float(user_input)
    except ValueError:
        logger.info("Invalid step size input by %s: %s", user.id, user_input)
        await update.message.reply_text(
            LANG_TEXTS[current_language]["invalid_step_size"]
            + " "
            + LANG_TEXTS[current_language]["try_again"]
        )
        return STEP_SIZE

    try:
        initial_x_value = float(context.user_data["initial_x"])
        reach_point_value = float(context.user_data["reach_point"])
        num_points = abs(reach_point_value - initial_x_value) / step_value

        if num_points > MAX_CALCULATION_POINTS:
            logger.info(
                "Too many calculation points for %s: %d", user.id, int(num_points)
            )
            await update.message.reply_text(
                LANG_TEXTS[current_language]["too_many_points"]
                + f"{int(num_points)}. "
                + LANG_TEXTS[current_language]["max_points_allowed"]
                + f"{MAX_CALCULATION_POINTS}. "
                + LANG_TEXTS[current_language]["try_again"]
            )
            return STEP_SIZE

    except Exception as e:
        logger.error("Error calculating number of points for %s: %s", user.id, e)

    logger.info("Step size of %s: %s", user.id, user_input)
    context.user_data["step_size"] = user_input

    return await solution(update, context)


async def solution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.edited_message:
        return STEP_SIZE

    user = update.message.from_user
    current_language = context.user_data.get("language", DEFAULT_LANGUAGE)

    processing_message = await update.message.reply_text("⏳")

    try:
        application_id = await set_parameters(
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
    except Exception as e:
        logger.error("Error while setting parameters: %s", e)
        await save_user_settings(context)
        await processing_message.edit_text(
            LANG_TEXTS[current_language]["server_error"]
            + " "
            + LANG_TEXTS[current_language]["try_again"],
            reply_markup=solution_markup(current_language),
        )
        return MENU

    asyncio.create_task(
        solution_completion_handle(
            application_id, context, processing_message, current_language
        )
    )

    return MENU


async def solution_completion_handle(application_id, context, message, lang):
    try:
        is_completed = await wait_for_application_completion(application_id)

        if not is_completed:
            await message.edit_text(
                LANG_TEXTS[lang]["processing_error"]
                + " "
                + LANG_TEXTS[lang]["try_again"],
                reply_markup=solution_markup(lang),
            )
            return

        results = await get_results(application_id)

        if not results:
            await message.edit_text(
                LANG_TEXTS[lang]["data_error"] + " " + LANG_TEXTS[lang]["try_again"],
                reply_markup=solution_markup(lang),
            )
            return

        data = json.loads(results[0].get("data", "{}"))

        x_values = data.get("xvalues", [])
        y_values = data.get("yvalues", [])
        solution = data.get("solution", "")

        if not solution:
            await message.edit_text(
                LANG_TEXTS[lang]["data_error"] + " " + LANG_TEXTS[lang]["try_again"],
                reply_markup=solution_markup(lang),
            )
            return

        plot_graph = plot_solution(x_values, y_values, context.user_data["order"])
        print_result = print_solution(
            solution, context.user_data["order"], context.user_data["rounding"]
        )

        try:
            await message.edit_media(
                media=InputMediaPhoto(plot_graph, caption=print_result),
                reply_markup=solution_markup(lang),
                write_timeout=60,
                pool_timeout=30,
            )
        except telegram.error.TimedOut:
            await message.edit_text(print_result, reply_markup=solution_markup(lang))
        finally:
            plot_graph.close()

        await save_user_settings(context)

    except Exception as e:
        logger.error("Unexpected error in background completion task: %s", e)
        await message.edit_text(
            LANG_TEXTS[lang]["server_error"] + " " + LANG_TEXTS[lang]["try_again"],
            reply_markup=solution_markup(lang),
        )


def solution_markup(language):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    LANG_TEXTS[language]["solve_over"], callback_data="solve"
                )
            ],
            [InlineKeyboardButton(LANG_TEXTS[language]["menu"], callback_data="menu")],
        ]
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_state = context.user_data.get("state", None)

    if current_state in [EQUATION, INITIAL_X, INITIAL_Y, REACH_POINT, STEP_SIZE]:
        user = update.message.from_user
        logger.info("User %s canceled solving", user.id)

        await save_user_settings(context)

        current_language = context.user_data.get("language", DEFAULT_LANGUAGE)

        keyboard = [
            [
                InlineKeyboardButton(
                    LANG_TEXTS[current_language]["solve_over"], callback_data="solve"
                )
            ],
            [
                InlineKeyboardButton(
                    LANG_TEXTS[current_language]["menu"], callback_data="menu"
                )
            ],
        ]

        new_reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            LANG_TEXTS[current_language]["cancel"], reply_markup=new_reply_markup
        )
        return MENU
    else:
        if update.message:
            await update.message.delete()
        return current_state


async def save_user_settings(context: ContextTypes.DEFAULT_TYPE):
    keys_to_keep = ["method", "rounding", "language", "hints"]
    for key in list(context.user_data.keys()):
        if key not in keys_to_keep:
            del context.user_data[key]


def main() -> None:
    application = Application.builder().token(os.getenv("CLIENT_API_KEY")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [
                CallbackQueryHandler(solve, pattern="^solve$"),
                CallbackQueryHandler(solve_history, pattern="^solve_history$"),
                CallbackQueryHandler(solve_history, pattern="^solve_history_back$"),
                CallbackQueryHandler(
                    solve_history_details, pattern=r"^application_\d+$"
                ),
                CallbackQueryHandler(start, pattern="^back$"),
                CallbackQueryHandler(start, pattern="^menu$"),
                CallbackQueryHandler(settings, pattern="^settings$"),
                CallbackQueryHandler(settings, pattern="^settings_back$"),
                CallbackQueryHandler(settings_method, pattern="^settings_method$"),
                CallbackQueryHandler(settings_rounding, pattern="^settings_rounding$"),
                CallbackQueryHandler(settings_language, pattern="^settings_language$"),
                CallbackQueryHandler(
                    method, pattern="^(euler|midpoint|heun|runge_kutta|dormand_prince)$"
                ),
                CallbackQueryHandler(rounding, pattern="^(4|6|8|16)$"),
                CallbackQueryHandler(language, pattern="^(en|ru|zh)$"),
                CallbackQueryHandler(hints, pattern="^(true|false)$"),
            ],
            EQUATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, equation)],
            INITIAL_X: [MessageHandler(filters.TEXT & ~filters.COMMAND, initial_x)],
            INITIAL_Y: [MessageHandler(filters.TEXT & ~filters.COMMAND, initial_y)],
            REACH_POINT: [MessageHandler(filters.TEXT & ~filters.COMMAND, reach_point)],
            STEP_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_size)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))

    application.run_polling(allowed_updates=Update.ALL_TYPES)
