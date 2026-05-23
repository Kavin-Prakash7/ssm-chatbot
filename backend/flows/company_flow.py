
from backend.services.company_service import search_entities
from backend.services.entity_division_service import get_entities_for_division
from backend.services.entity_document_service import build_entity_document_response
from backend.services.response_service import build_button, build_card, create_response
from backend.utils.helpers import copy_for
from backend.utils.state_manager import get_state, update_state
from backend.utils.translations import DIVISION_COPY


INTRO_LIMIT = 4


def _lang_key(language):
    return "ms" if language == "ms" else "en"


def _build_company_intro(language):
    entities = get_entities_for_division("companies", limit=INTRO_LIMIT)
    content = DIVISION_COPY["companies"][_lang_key(language)]

    cards = []
    select_label = "Select" if _lang_key(language) == "en" else "Pilih"
    for entity in entities:
        cards.append(
            build_card(
                f"company_intro:{entity['name']}",
                entity["name"],
                subtitle=entity["type"],
                actions=[build_button(f"select_company:{entity['name']}", select_label, "secondary")],
            )
        )

    buttons = [
        build_button(
            "company_enter_query",
            "Continue Company Search" if _lang_key(language) == "en" else "Teruskan Carian Syarikat",
        ),
        build_button("main_menu", "Main Menu" if _lang_key(language) == "en" else "Menu Utama", "secondary"),
    ]

    return create_response(
        response_type="division_entities",
        title=content["title"],
        message=content["message"],
        cards=cards,
        buttons=buttons,
        data={"division": "companies"},
    )


def _build_results(query, page, language):
    results, total = search_entities(query, page=page)
    if not results:
        return create_response(
            response_type="company",
            title="Search",
            message=copy_for(language, "no_results"),
            buttons=[build_button("main_menu", "Main Menu" if _lang_key(language) == "en" else "Menu Utama")],
        )

    cards = []
    for item in results:
        cards.append(
            build_card(
                f"company:{item['name']}",
                item["name"],
                subtitle=item["type"],
                actions=[
                    build_button(
                        f"select_company:{item['name']}",
                        "Select" if _lang_key(language) == "en" else "Pilih",
                    )
                ],
            )
        )

    buttons = [build_button("main_menu", "Main Menu" if _lang_key(language) == "en" else "Menu Utama")]
    if total > page * 5:
        buttons.append(
            build_button(
                "company_more",
                "See more" if _lang_key(language) == "en" else "Lihat lagi",
                "secondary",
            )
        )
    results_message = (
        f"{len(results)} / {total} results"
        if _lang_key(language) == "en"
        else f"{len(results)} / {total} keputusan"
    )
    return create_response(
        response_type="company",
        title=copy_for(language, "results_title"),
        message=results_message,
        cards=cards,
        buttons=buttons,
    )


def handle_company_flow(session_id, message, action, language):
    state = get_state(session_id)
    step = state.get("step")
    context = state.get("context", {})

    if action == "check_company" or step == "ask_name":
        update_state(session_id, {"step": "awaiting_query", "context": {}})
        return _build_company_intro(language)

    if action == "company_enter_query":
        update_state(session_id, {"step": "awaiting_query"})
        return create_response(
            response_type="company",
            title="Company Search" if _lang_key(language) == "en" else "Carian Syarikat",
            message=copy_for(language, "ask_company"),
            buttons=[build_button("main_menu", "Main Menu" if _lang_key(language) == "en" else "Menu Utama")],
        )

    if message:
        query = message.strip()
        update_state(session_id, {"step": "show_results", "context": {"query": query, "page": 1}})
        return _build_results(query, 1, language)

    if action == "company_more":
        query = context.get("query")
        if not query:
            return create_response(
                response_type="company",
                title="Company Search",
                message=copy_for(language, "ask_company"),
                buttons=[build_button("main_menu", "Main Menu" if language == "en" else "Menu Utama")],
            )
        page = context.get("page", 1) + 1
        update_state(session_id, {"context": {"query": query, "page": page}})
        return _build_results(query, page, language)

    if action.startswith("select_company:"):
        name = action.split(":", 1)[1]
        return build_entity_document_response(session_id, language, "companies", name)

    return _build_company_intro(language)
