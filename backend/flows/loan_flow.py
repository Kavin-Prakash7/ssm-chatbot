
from backend.services.response_service import build_button, build_card, create_response
from backend.utils.helpers import copy_for
from backend.utils.state_manager import add_to_cart, get_state, update_state


BANKS = ["Maybank", "CIMB", "Public Bank"]

LOAN_DOCUMENTS = [
    {
        "id": "company_profile",
        "name": "Company Profile (CTC)",
        "best_for": "Company overview",
        "note": "Shows company status and directors",
        "ctc_price": "RM 50",
        "non_ctc_price": "RM 20",
    },
    {
        "id": "certificate_incorporation",
        "name": "Certificate of Incorporation",
        "best_for": "Legal proof",
        "note": "Legal proof of registration",
        "ctc_price": "RM 65",
        "non_ctc_price": "RM 30",
    },
    {
        "id": "register_directors",
        "name": "Register of Directors",
        "best_for": "Director verification",
        "note": "Required for director verification",
        "ctc_price": "RM 60",
        "non_ctc_price": "RM 28",
    },
]


def handle_loan_flow(session_id, message, action, language):
    state = get_state(session_id)
    step = state.get("step")
    context = state.get("context", {})

    if action.startswith("bank:"):
        bank = action.split(":", 1)[1]
        update_state(
            session_id,
            {
                "step": "recommendations",
                "context": {"bank": bank},
                "completed": True,
            },
        )
        cards = []
        for doc in LOAN_DOCUMENTS:
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
                ),
            ]
            cards.append(
                build_card(
                    doc["id"],
                    doc["name"],
                    subtitle=doc.get("best_for", ""),
                    meta={"note": doc["note"]},
                    actions=actions,
                    pricing={"ctc": doc["ctc_price"], "non_ctc": doc["non_ctc_price"]},
                )
            )
        return create_response(
            response_type="loan",
            title="Loan Documents",
            message=copy_for(language, "loan_recommendation").format(bank=bank),
            cards=cards,
            buttons=[build_button("main_menu", "Main Menu" if language == "en" else "Menu Utama")],
        )

    if action.startswith("preview:"):
        return create_response(
            response_type="loan",
            title="Preview",
            message=copy_for(language, "preview_ready"),
            buttons=[build_button("main_menu", "Main Menu" if language == "en" else "Menu Utama")],
        )

    if action.startswith("add_to_cart:"):
        doc_id = action.split(":", 1)[1]
        add_to_cart(session_id, {"document_id": doc_id})
        return create_response(
            response_type="loan",
            title="Cart",
            message=copy_for(language, "added_to_cart"),
            buttons=[
                build_button("main_menu", "Main Menu" if language == "en" else "Menu Utama"),
                build_button("loan_from_bank", "More Bank Docs" if language == "en" else "Tambah Dokumen"),
            ],
        )

    if action == "loan_from_bank":
        update_state(session_id, {"step": "select_bank", "context": {}, "completed": False})
        buttons = [build_button(f"bank:{bank}", bank) for bank in BANKS]
        return create_response(
            response_type="loan",
            title="Loan",
            message=copy_for(language, "select_bank"),
            buttons=buttons,
        )

    if step == "recommendations" and context.get("bank"):
        bank = context.get("bank")
        cards = []
        for doc in LOAN_DOCUMENTS:
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
                ),
            ]
            cards.append(
                build_card(
                    doc["id"],
                    doc["name"],
                    subtitle=doc.get("best_for", ""),
                    meta={"note": doc["note"]},
                    actions=actions,
                    pricing={"ctc": doc["ctc_price"], "non_ctc": doc["non_ctc_price"]},
                )
            )
        return create_response(
            response_type="loan",
            title="Loan Documents",
            message=copy_for(language, "loan_recommendation").format(bank=bank),
            cards=cards,
            buttons=[build_button("main_menu", "Main Menu" if language == "en" else "Menu Utama")],
        )

    if step == "select_bank" or not step:
        update_state(session_id, {"step": "select_bank", "completed": False})
        buttons = [build_button(f"bank:{bank}", bank) for bank in BANKS]
        return create_response(
            response_type="loan",
            title="Loan",
            message=copy_for(language, "select_bank"),
            buttons=buttons,
        )

    return create_response(
        response_type="loan",
        title="Loan",
        message=copy_for(language, "select_bank"),
        buttons=[build_button(f"bank:{bank}", bank) for bank in BANKS],
    )
