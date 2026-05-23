
from backend.utils.helpers import copy_for


def create_response(
    response_type="info",
    title="",
    message="",
    buttons=None,
    cards=None,
    suggestions=None,
    data=None,
):
    return {
        "success": True,
        "type": response_type,
        "title": title,
        "message": message,
        "buttons": buttons or [],
        "cards": cards or [],
        "suggestions": suggestions or [],
        "data": data or {},
    }


def build_button(button_id, label, style="primary"):
    return {"id": button_id, "label": label, "style": style}


def build_card(card_id, title, subtitle="", meta=None, actions=None, pricing=None):
    return {
        "id": card_id,
        "title": title,
        "subtitle": subtitle,
        "meta": meta or {},
        "actions": actions or [],
        "pricing": pricing or {},
    }


def build_main_menu_response(language):
    buttons = [
        build_button("get_documents", "Get Documents" if language == "en" else "Dapatkan Dokumen"),
        build_button("loan_from_bank", "Loan from Bank" if language == "en" else "Pinjaman Bank"),
        build_button("check_company", "Check Company" if language == "en" else "Semak Syarikat"),
        build_button("view_pricing", "View Pricing" if language == "en" else "Lihat Harga"),
    ]
    suggestions = [
        build_button("faq:ctc_vs_non_ctc", "CTC vs Non-CTC" if language == "en" else "CTC vs Non-CTC", "chip"),
        build_button(
            "faq:loan_documents",
            "Loan documents required" if language == "en" else "Dokumen pinjaman",
            "chip",
        ),
        build_button(
            "faq:company_status",
            "Check company status" if language == "en" else "Semak status syarikat",
            "chip",
        ),
        build_button(
            "faq:director_involvement",
            "Director involvement" if language == "en" else "Penglibatan pengarah",
            "chip",
        ),
    ]
    return create_response(
        response_type="menu",
        title=copy_for(language, "menu_title"),
        message=copy_for(language, "welcome"),
        buttons=buttons,
        suggestions=suggestions,
    )


def build_pricing_response(language):
    pricing_cards = [
        {
            "id": "company_profile",
            "title": "Company Profile",
            "subtitle": "Core company snapshot",
            "note": "Best for quick verification",
            "pricing": {"ctc": "RM 50", "non_ctc": "RM 20"},
        },
        {
            "id": "register_directors",
            "title": "Register of Directors",
            "subtitle": "Directorship verification",
            "note": "Validate current directors",
            "pricing": {"ctc": "RM 60", "non_ctc": "RM 30"},
        },
        {
            "id": "financial_statements",
            "title": "Financial Statements",
            "subtitle": "Latest audited figures",
            "note": "Ideal for credit review",
            "pricing": {"ctc": "RM 70", "non_ctc": "RM 35"},
        },
    ]

    cards = []
    for card in pricing_cards:
        actions = [
            build_button(
                f"preview:{card['id']}:non_ctc",
                "View Non-CTC" if language == "en" else "Lihat Non-CTC",
                "secondary",
            ),
            build_button(
                f"preview:{card['id']}:ctc",
                "View CTC" if language == "en" else "Lihat CTC",
                "secondary",
            ),
            build_button(
                f"add_to_cart:{card['id']}",
                "Add to Cart" if language == "en" else "Tambah ke Troli",
            ),
        ]
        cards.append(
            build_card(
                card["id"],
                card["title"],
                subtitle=card["subtitle"],
                meta={"note": card["note"]},
                actions=actions,
                pricing=card["pricing"],
            )
        )

    return create_response(
        response_type="pricing",
        title="Pricing",
        message=copy_for(language, "pricing_intro"),
        cards=cards,
        buttons=[build_button("main_menu", "Main Menu" if language == "en" else "Menu Utama")],
    )
