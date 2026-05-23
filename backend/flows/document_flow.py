
from backend.services.document_service import (
    get_documents_for_purpose,
    get_purpose_copy,
    get_purpose_label,
    get_purpose_options,
)
from backend.services.response_service import build_button, build_card, create_response
from backend.utils.helpers import copy_for
from backend.utils.state_manager import add_to_cart, get_state, update_state


def build_document_cards(documents, language):
    cards = []
    for doc in documents:
        actions = [
            build_button(
                f"preview:{doc['id']}:non_ctc",
                "View Non-CTC" if language == "en" else "Lihat Non-CTC",
                "secondary",
            ),
            build_button(
                f"preview:{doc['id']}:ctc",
                "View CTC" if language == "en" else "Lihat CTC",
                "secondary",
            ),
            build_button(
                f"add_to_cart:{doc['id']}",
                "Add to Cart" if language == "en" else "Tambah ke Troli",
                "primary",
            ),
        ]
        cards.append(
            build_card(
                doc["id"],
                doc["name"],
                subtitle=doc["best_for"],
                meta={"note": doc["note"]},
                actions=actions,
                pricing={"ctc": doc["ctc_price"], "non_ctc": doc["non_ctc_price"]},
            )
        )
    return cards


def build_document_cards_response(language, title, message, documents, buttons=None):
    cards = build_document_cards(documents, language)
    final_buttons = buttons or [build_button("main_menu", "Main Menu" if language == "en" else "Menu Utama")]
    return create_response(
        response_type="documents",
        title=title,
        message=message,
        cards=cards,
        buttons=final_buttons,
    )


def handle_document_flow(session_id, message, action, language):
    state = get_state(session_id)
    step = state.get("step")
    context = state.get("context", {})

    if action.startswith("purpose:"):
        purpose_key = action.split(":", 1)[1]
        update_state(
            session_id,
            {
                "step": "recommendations",
                "context": {"purpose": purpose_key},
                "completed": True,
            },
        )
        documents = get_documents_for_purpose(purpose_key)
        purpose_label = get_purpose_label(purpose_key, language)
        purpose_copy = get_purpose_copy(purpose_key, language)
        return build_document_cards_response(
            language,
            purpose_copy["title"] or "Recommendations",
            purpose_copy["description"] or copy_for(language, "doc_recommendations").format(purpose=purpose_label),
            documents,
        )

    if action.startswith("preview:"):
        return create_response(
            response_type="documents",
            title="Preview",
            message=copy_for(language, "preview_ready"),
            buttons=[build_button("main_menu", "Main Menu" if language == "en" else "Menu Utama")],
        )

    if action.startswith("add_to_cart:"):
        doc_id = action.split(":", 1)[1]
        add_to_cart(session_id, {"document_id": doc_id})
        return create_response(
            response_type="documents",
            title="Cart",
            message=copy_for(language, "added_to_cart"),
            buttons=[
                build_button("main_menu", "Main Menu" if language == "en" else "Menu Utama"),
                build_button("get_documents", "Get More" if language == "en" else "Tambah Lagi"),
            ],
        )

    if action == "get_documents":
        update_state(session_id, {"step": "purpose", "context": {}, "completed": False})
        buttons = [build_button(option["id"], option["label"]) for option in get_purpose_options(language)]
        return create_response(
            response_type="documents",
            title="Documents",
            message=copy_for(language, "ask_purpose"),
            buttons=buttons,
        )

    if step == "recommendations" and context.get("purpose"):
        purpose_key = context.get("purpose")
        documents = get_documents_for_purpose(purpose_key)
        purpose_label = get_purpose_label(purpose_key, language)
        purpose_copy = get_purpose_copy(purpose_key, language)
        return build_document_cards_response(
            language,
            purpose_copy["title"] or "Recommendations",
            purpose_copy["description"] or copy_for(language, "doc_recommendations").format(purpose=purpose_label),
            documents,
        )

    if step == "purpose" or not step:
        update_state(session_id, {"step": "purpose", "completed": False})
        buttons = [build_button(option["id"], option["label"]) for option in get_purpose_options(language)]
        return create_response(
            response_type="documents",
            title="Documents",
            message=copy_for(language, "ask_purpose"),
            buttons=buttons,
        )

    return build_document_cards_response(
        language,
        "Documents",
        copy_for(language, "ask_purpose"),
        [],
        buttons=[build_button(option["id"], option["label"]) for option in get_purpose_options(language)],
    )
