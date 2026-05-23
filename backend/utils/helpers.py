
import json
import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))


def load_json(relative_path):
    file_path = os.path.join(BASE_DIR, relative_path)
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(text):
    return " ".join(text.strip().lower().split())


LANG_COPY = {
    "en": {
        "welcome": "Welcome to SSM eInfo Assistant. Choose a service to continue.",
        "menu_title": "How can I help you today?",
        "ask_purpose": "What is the purpose for the documents?",
        "doc_recommendations": "Here are recommended documents for {purpose}.",
        "ask_company": "Please enter the company name to search.",
        "results_title": "Select a company from the results.",
        "no_results": "No matches found. Try another name.",
        "select_bank": "Select your bank so I can recommend required SSM documents.",
        "loan_recommendation": "For {bank}, these documents are commonly requested.",
        "added_to_cart": "Added to cart.",
        "pricing_intro": "Here is a quick pricing overview before checkout.",
        "preview_ready": "Preview noted. You can add this document to your cart when ready.",
    },
    "ms": {
        "welcome": "Selamat datang ke SSM eInfo Assistant. Pilih perkhidmatan untuk teruskan.",
        "menu_title": "Bagaimana saya boleh bantu hari ini?",
        "ask_purpose": "Apakah tujuan mendapatkan dokumen?",
        "doc_recommendations": "Berikut ialah dokumen yang disyorkan untuk {purpose}.",
        "ask_company": "Sila masukkan nama syarikat untuk carian.",
        "results_title": "Pilih syarikat daripada keputusan.",
        "no_results": "Tiada padanan ditemui. Cuba nama lain.",
        "select_bank": "Pilih bank anda supaya saya cadangkan dokumen SSM diperlukan.",
        "loan_recommendation": "Untuk {bank}, dokumen berikut biasanya diminta.",
        "added_to_cart": "Ditambah ke troli.",
        "pricing_intro": "Berikut ialah ringkasan harga sebelum pembayaran.",
        "preview_ready": "Pratonton direkodkan. Anda boleh tambah dokumen ini ke troli bila bersedia.",
    },
}


def copy_for(language, key):
    return LANG_COPY.get(language, LANG_COPY["en"]).get(key, "")
