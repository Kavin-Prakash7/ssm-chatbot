
from backend.services.faq_service import get_answer
from backend.services.response_service import create_response, build_button


FAQ_MAP = {
    "faq:ctc_vs_non_ctc": "What is the difference between CTC and Non-CTC documents?",
    "faq:loan_documents": "Which document is required to open a corporate bank account in Malaysia?",
    "faq:company_status": "How can I check if a company is still active or has been dissolved?",
    "faq:director_involvement": "How do I verify a director's involvement in multiple companies?",
}

FAQ_TRANSLATIONS = {
    "faq:ctc_vs_non_ctc": {
        "ms": "CTC (Salinan Benar Disahkan) disahkan secara digital dan diterima oleh bank. Non-CTC adalah untuk rujukan sahaja.",
    },
    "faq:loan_documents": {
        "ms": "Bank biasanya memerlukan CTC Profil Syarikat dan Sijil Pemerbadanan untuk pengesahan syarikat.",
    },
    "faq:company_status": {
        "ms": "Anda boleh membeli Profil Syarikat di SSM e-Info untuk melihat status semasa (wujud/dibubarkan).",
    },
    "faq:director_involvement": {
        "ms": "Gunakan Register of Directors atau carian directorship untuk melihat penglibatan pengarah di syarikat lain.",
    },
}


def handle_faq(action_id, language):
    question = FAQ_MAP.get(action_id)
    answer = None
    if language == "ms":
        answer = FAQ_TRANSLATIONS.get(action_id, {}).get("ms")
    if not answer and question:
        answer = get_answer(question, language)
    if not answer:
        answer = (
            "I can help with SSM eInfo documents and company searches."
            if language == "en"
            else "Saya boleh bantu dengan dokumen SSM eInfo dan carian syarikat."
        )
    return create_response(
        response_type="faq",
        title="FAQ",
        message=answer,
        buttons=[build_button("main_menu", "Main Menu" if language == "en" else "Menu Utama")],
    )
