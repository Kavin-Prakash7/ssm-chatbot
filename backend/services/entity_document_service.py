from backend.services.document_service import get_documents_for_division
from backend.services.response_service import build_button
from backend.utils.state_manager import update_state
from backend.utils.translations import DIVISION_DOCUMENT_COPY


def _lang_key(language):
    return "ms" if language == "ms" else "en"


def _copy_for_division(division, language):
    lang = _lang_key(language)
    copy_block = DIVISION_DOCUMENT_COPY.get(division, {}).get(lang)
    if copy_block:
        return copy_block
    if lang == "en":
        return {
            "title": "Documents",
            "message": "Here are recommended documents for {entity}.",
        }
    return {
        "title": "Dokumen",
        "message": "Berikut dokumen yang disyorkan untuk {entity}.",
    }


def build_entity_document_response(session_id, language, division, entity_name):
    from backend.flows.document_flow import build_document_cards_response

    lang = _lang_key(language)
    documents = get_documents_for_division(division)
    update_state(
        session_id,
        {
            "selected_entity": {"name": entity_name, "division": division},
        },
    )
    if not documents:
        return None

    update_state(
        session_id,
        {
            "flow": "documents",
            "step": "recommendations",
            "context": {"division": division, "entity": entity_name},
            "pending_intent": None,
        },
    )

    copy_block = _copy_for_division(division, language)
    buttons = [
        build_button(
            "get_documents",
            "More Documents" if lang == "en" else "Dokumen Lain",
            "secondary",
        ),
        build_button("main_menu", "Main Menu" if lang == "en" else "Menu Utama"),
    ]
    return build_document_cards_response(
        language,
        copy_block["title"],
        copy_block["message"].format(entity=entity_name),
        documents,
        buttons=buttons,
    )
