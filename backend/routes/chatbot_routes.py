
from urllib.parse import quote_plus, unquote_plus

import os

from flask import Blueprint, jsonify, render_template, request, send_from_directory

from backend.flows.company_flow import handle_company_flow
from backend.flows.document_flow import handle_document_flow
from backend.flows.faq_flow import handle_faq
from backend.flows.loan_flow import handle_loan_flow
from backend.services.entity_division_service import (
    detect_division as detect_entity_division,
    get_division_flow_action,
    get_entities_for_division,
)
from backend.services.entity_document_service import build_entity_document_response
from backend.services.llm_service import handle_llm_message
from backend.services.response_service import (
    build_button,
    build_card,
    build_main_menu_response,
    build_pricing_response,
    create_response,
)
from backend.utils.intent_detector import detect_intent
from backend.utils.language_detector import detect_language
from backend.utils.state_manager import (
    get_or_create_session,
    get_state,
    reset_flow,
    update_state,
)
from backend.utils.translations import DIVISION_COPY

chatbot_bp = Blueprint("chatbot", __name__)

SAMPLE_PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sample_pdfs")

FLOW_ACTION_TO_STATE = {
    "get_documents": "documents",
    "check_company": "company",
    "loan_from_bank": "loan",
}


FLOW_INTENT_TO_DIVISION = {
    "loan": "banks",
    "company": "companies",
}

FLOW_STATE_TO_DIVISION = {
    "loan": "banks",
    "company": "companies",
}

def _resolve_language(language):
    return "ms" if language == "ms" else "en"

FLOW_COPY = {
    "get_documents": {
        "en": {
            "title": "Document Guidance",
            "message": "📄 I can help you find the right SSM documents.\n\nWould you like to continue?",
            "continue_label": "Continue Document Flow",
            "suggestion_label": "Document Guidance",
        },
        "ms": {
            "title": "Panduan Dokumen",
            "message": "📄 Saya boleh bantu anda mencari dokumen SSM yang sesuai.\n\nAdakah anda ingin teruskan?",
            "continue_label": "Teruskan Aliran Dokumen",
            "suggestion_label": "Panduan Dokumen",
        },
    },
    "check_company": {
        "en": {
            "title": "Company Search",
            "message": "🏢 I can help you search for company information.\n\nWould you like to continue?",
            "continue_label": "Continue Company Search",
            "suggestion_label": "Company Search",
        },
        "ms": {
            "title": "Carian Syarikat",
            "message": "🏢 Saya boleh bantu anda mencari maklumat syarikat.\n\nAdakah anda ingin teruskan?",
            "continue_label": "Teruskan Carian Syarikat",
            "suggestion_label": "Carian Syarikat",
        },
    },
    "loan_from_bank": {
        "en": {
            "title": "Loan Support",
            "message": "🏦 I can help with bank-loan document guidance.\n\nWould you like to continue?",
            "continue_label": "Continue Loan Flow",
            "suggestion_label": "Loan Support",
        },
        "ms": {
            "title": "Bantuan Pinjaman",
            "message": "🏦 Saya boleh bantu dengan panduan dokumen pinjaman bank.\n\nAdakah anda ingin teruskan?",
            "continue_label": "Teruskan Aliran Pinjaman",
            "suggestion_label": "Bantuan Pinjaman",
        },
    },
}


@chatbot_bp.route("/")
def index():
    return render_template("index.html")


@chatbot_bp.route("/checkout")
def checkout():
    return render_template("checkout.html")


@chatbot_bp.route("/sample-pdf/<path:filename>")
def sample_pdf(filename):
    safe_name = os.path.basename(filename)
    if not safe_name.endswith(".pdf"):
        return jsonify({"error": "Invalid file"}), 404
    file_path = os.path.join(SAMPLE_PDF_DIR, safe_name)
    if not os.path.exists(file_path):
        return jsonify({"error": "PDF not found"}), 404
    return send_from_directory(SAMPLE_PDF_DIR, safe_name)


def _attach_session(response, session_id, language):
    response.setdefault("data", {})
    response["data"].update({"session_id": session_id, "language": language})
    return response


def _flow_content(language, action):
    lang_key = _resolve_language(language)
    return FLOW_COPY[action][lang_key]


def _build_flow_confirmation_response(language, pending_intent):
    action = pending_intent.get("action")
    content = _flow_content(language, action)
    return create_response(
        response_type="intent_confirmation",
        title=content["title"],
        message=content["message"],
        buttons=[
            build_button(f"confirm_intent:{action}", content["continue_label"]),
            build_button("main_menu", "Main Menu" if language == "en" else "Menu Utama", "secondary"),
        ],
        data={"pending_intent": pending_intent},
    )


def _build_intent_suggestion_response(session_id, language, detected_intent):
    suggestions = detected_intent.get("suggestions", [])
    buttons = [
        build_button(
            f"review_intent:{suggestion['action']}",
            _flow_content(language, suggestion["action"])["suggestion_label"],
            "secondary",
        )
        for suggestion in suggestions
    ]
    buttons.append(build_button("main_menu", "Main Menu" if language == "en" else "Menu Utama"))
    update_state(session_id, {"pending_intent": None})
    return create_response(
        response_type="intent_suggestion",
        title="Suggested Next Step" if language == "en" else "Cadangan Langkah Seterusnya",
        message=(
            "I found a few possible directions. Please choose the one you want to continue with."
            if language == "en"
            else "Saya menemui beberapa kemungkinan. Sila pilih yang anda mahu teruskan."
        ),
        buttons=buttons,
        data={"suggestions": suggestions},
    )


def _build_flow_lock_response(language, active_flow, target_label=None):
    active_action = next(action for action, flow in FLOW_ACTION_TO_STATE.items() if flow == active_flow)
    active_label = _flow_content(language, active_action)["suggestion_label"]
    if target_label:
        message = (
            f"You are currently in {active_label}. To switch to {target_label}, please return to the Main Menu first."
            if language == "en"
            else f"Anda sedang berada dalam {active_label}. Untuk beralih ke {target_label}, sila kembali ke Menu Utama dahulu."
        )
    else:
        message = (
            f"You are currently in {active_label}. Please continue this flow or return to the Main Menu first."
            if language == "en"
            else f"Anda sedang berada dalam {active_label}. Sila teruskan aliran ini atau kembali ke Menu Utama dahulu."
        )
    return create_response(
        response_type="flow_locked",
        title="Flow Locked" if language == "en" else "Aliran Dikunci",
        message=message,
        buttons=[
            build_button("resume_flow", "Continue Current Flow" if language == "en" else "Teruskan Aliran Semasa"),
            build_button("main_menu", "Main Menu" if language == "en" else "Menu Utama", "secondary"),
        ],
        data={"active_flow": active_flow},
    )


def _division_lang(language):
    return _resolve_language(language)


def _division_content(language, division):
    lang_key = _division_lang(language)
    return DIVISION_COPY[division][lang_key]


def _build_division_response(session_id, language, division):
    entities = get_entities_for_division(division)
    if not entities:
        return None

    content = _division_content(language, division)
    cards = []
    select_label = "Select" if _resolve_language(language) == "en" else "Pilih"
    for entity in entities:
        encoded_name = quote_plus(entity["name"])
        encoded_division = quote_plus(division)
        cards.append(
            build_card(
                f"division_card:{division}:{entity['name']}",
                entity["name"],
                subtitle=entity["type"],
                actions=[
                    build_button(
                        f"division_select:{encoded_division}:{encoded_name}",
                        select_label,
                        "secondary",
                    )
                ],
            )
        )

    buttons = [
        build_button(
            "main_menu",
            "Main Menu" if _resolve_language(language) == "en" else "Menu Utama",
        )
    ]
    flow_action = get_division_flow_action(division)
    if flow_action and flow_action in FLOW_ACTION_TO_STATE:
        pending_intent = {
            "intent": FLOW_ACTION_TO_STATE[flow_action],
            "action": flow_action,
            "kind": "flow",
            "confidence": "high",
        }
        update_state(session_id, {"pending_intent": pending_intent})
        continue_label = _flow_content(language, flow_action)["continue_label"]
        buttons.insert(0, build_button(f"confirm_intent:{flow_action}", continue_label))

    return create_response(
        response_type="division_entities",
        title=content["title"],
        message=content["message"],
        cards=cards,
        buttons=buttons,
        data={"division": division},
    )


def _handle_division_selection(session_id, action, language):
    try:
        _, encoded_division, encoded_name = action.split(":", 2)
    except ValueError:
        return build_main_menu_response(language)

    division = unquote_plus(encoded_division)
    entity_name = unquote_plus(encoded_name)
    response = build_entity_document_response(session_id, language, division, entity_name)
    if response:
        return response
    return build_main_menu_response(language)


def _maybe_lock_flow_action(session_id, action, language):
    active_flow = get_state(session_id).get("flow", "idle")
    target_flow = FLOW_ACTION_TO_STATE.get(action)
    if active_flow in (None, "idle") or not target_flow or active_flow == target_flow:
        return None
    if {active_flow, target_flow} == {"documents", "company"}:
        return None
    target_label = _flow_content(language, action)["suggestion_label"]
    return _build_flow_lock_response(language, active_flow, target_label)


def _run_flow_action(session_id, message, action, language):
    update_state(session_id, {"pending_intent": None})
    if action == "view_pricing":
        return build_pricing_response(language)
    if action == "get_documents":
        update_state(session_id, {"flow": "documents", "step": "purpose", "completed": False})
        return handle_document_flow(session_id, message, action, language)
    if action == "check_company":
        update_state(session_id, {"flow": "company", "step": "ask_name", "completed": False})
        return handle_company_flow(session_id, message, action, language)
    if action == "loan_from_bank":
        update_state(session_id, {"flow": "loan", "step": "select_bank", "completed": False})
        return handle_loan_flow(session_id, message, action, language)
    return None


def _resume_flow(session_id, language):
    flow = get_state(session_id).get("flow", "idle")
    if flow == "documents":
        return handle_document_flow(session_id, "", "", language)
    if flow == "company":
        return handle_company_flow(session_id, "", "", language)
    if flow == "loan":
        return handle_loan_flow(session_id, "", "", language)
    return build_main_menu_response(language)


def _review_intent_action(session_id, action, language):
    flow_action = action.split(":", 1)[1]
    if flow_action not in FLOW_ACTION_TO_STATE:
        return build_main_menu_response(language)
    pending_intent = {
        "intent": FLOW_ACTION_TO_STATE[flow_action],
        "action": flow_action,
        "kind": "flow",
        "confidence": "medium",
    }
    update_state(session_id, {"pending_intent": pending_intent})
    return _build_flow_confirmation_response(language, pending_intent)


def _confirm_pending_intent(session_id, action, language):
    flow_action = action.split(":", 1)[1]
    pending_intent = get_state(session_id).get("pending_intent") or {}
    if pending_intent.get("action") != flow_action:
        if flow_action in FLOW_ACTION_TO_STATE:
            pending_intent = {
                "intent": FLOW_ACTION_TO_STATE[flow_action],
                "action": flow_action,
                "kind": "flow",
                "confidence": "high",
            }
            update_state(session_id, {"pending_intent": pending_intent})
            return _build_flow_confirmation_response(language, pending_intent)
        return build_main_menu_response(language)
    return _run_flow_action(session_id, "", flow_action, language)


def _build_guided_menu_response(language, intent_name):
    response = build_main_menu_response(language)

    if intent_name == "greeting":
        response["type"] = "greeting"
        response["title"] = "Welcome" if language == "en" else "Selamat Datang"
        response["message"] = (
            "Welcome. I can guide you to documents, company checks, pricing, or bank-loan preparation right away."
            if language == "en"
            else "Selamat datang. Saya boleh bantu anda terus ke dokumen, semakan syarikat, harga, atau persediaan pinjaman bank."
        )
        return response

    if intent_name == "onboarding":
        response["type"] = "onboarding"
        response["title"] = "Getting Started" if language == "en" else "Panduan Permulaan"
        response["message"] = (
            "I can guide you step by step. Choose documents, company search, pricing, or loan support to continue."
            if language == "en"
            else "Saya boleh pandu anda langkah demi langkah. Pilih dokumen, carian syarikat, harga, atau bantuan pinjaman untuk teruskan."
        )
        return response

    response["type"] = "faq"
    response["title"] = "Quick Help" if language == "en" else "Bantuan Pantas"
    response["message"] = (
        "Here are the most common SSM eInfo questions I can help with immediately."
        if language == "en"
        else "Berikut ialah soalan SSM eInfo yang paling biasa dan saya boleh bantu terus."
    )
    return response


def _handle_detected_intent(session_id, detected_intent, language, division=None):
    if not detected_intent:
        return None

    action = detected_intent.get("action")
    kind = detected_intent.get("kind")
    intent_name = detected_intent.get("intent")

    if action and action.startswith("faq:"):
        update_state(session_id, {"pending_intent": None})
        return handle_faq(action, language)

    if action == "faq_general":
        update_state(session_id, {"pending_intent": None})
        return _build_guided_menu_response(language, "faq")

    if intent_name in ("greeting", "onboarding"):
        update_state(session_id, {"pending_intent": None})
        return _build_guided_menu_response(language, intent_name)

    if action == "view_pricing":
        update_state(session_id, {"pending_intent": None})
        return build_pricing_response(language)

    if kind == "flow" and action in FLOW_ACTION_TO_STATE:
        division_from_intent = division or FLOW_INTENT_TO_DIVISION.get(intent_name)
        if division_from_intent:
            division_response = _build_division_response(session_id, language, division_from_intent)
            if division_response:
                return division_response
        update_state(session_id, {"pending_intent": detected_intent})
        return _build_flow_confirmation_response(language, detected_intent)

    if kind == "suggestion":
        return _build_intent_suggestion_response(session_id, language, detected_intent)

    return None


def _maybe_lock_active_flow(session_id, message, language):
    state = get_state(session_id)
    active_flow = state.get("flow", "idle")
    if active_flow in (None, "idle") or not message:
        return None

    detected_intent = detect_intent(message)
    if not detected_intent:
        return None

    if detected_intent.get("kind") != "flow" and detected_intent.get("kind") != "suggestion":
        return None

    intent_name = detected_intent.get("intent")
    if intent_name == active_flow:
        return None

    if detected_intent.get("kind") == "suggestion":
        other_suggestions = [
            suggestion
            for suggestion in detected_intent.get("suggestions", [])
            if suggestion.get("intent") != active_flow
        ]
        if other_suggestions:
            target_label = _flow_content(language, other_suggestions[0]["action"])["suggestion_label"]
            return _build_flow_lock_response(language, active_flow, target_label)
        return None

    target_label = None
    if detected_intent.get("action") in FLOW_COPY:
        target_label = _flow_content(language, detected_intent["action"])["suggestion_label"]
    return _build_flow_lock_response(language, active_flow, target_label)


def _should_interrupt_flow(active_flow, detected_intent):
    if active_flow in (None, "idle"):
        return False
    if not detected_intent or detected_intent.get("kind") != "flow":
        return False
    if detected_intent.get("confidence") != "high":
        return False
    intent_flow = detected_intent.get("intent")
    return intent_flow and intent_flow != active_flow


@chatbot_bp.route("/api/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    session_id = payload.get("session_id")
    message = (payload.get("message") or "").strip()
    action = (payload.get("action") or "").strip()

    session_id = get_or_create_session(session_id)
    state = get_state(session_id)
    flow = state.get("flow", "idle")

    detected_language = detect_language(message) if message else None
    detected_intent = detect_intent(message) if message else None
    division = detect_entity_division(message) if message else None

    if message and detected_language:
        update_state(session_id, {"language": detected_language})

    if _should_interrupt_flow(flow, detected_intent):
        reset_flow(session_id)
        flow = "idle"
        if detected_language:
            update_state(session_id, {"language": detected_language})

    state = get_state(session_id)
    language = detected_language or state.get("language") or "en"

    flow = state.get("flow", "idle")

    if action == "main_menu":
        reset_flow(session_id)
        response = build_main_menu_response(language)
        return jsonify(_attach_session(response, session_id, language))

    if action == "resume_flow":
        response = _resume_flow(session_id, language)
        return jsonify(_attach_session(response, session_id, language))

    if action.startswith("review_intent:"):
        response = _review_intent_action(session_id, action, language)
        return jsonify(_attach_session(response, session_id, language))

    if action.startswith("confirm_intent:"):
        response = _confirm_pending_intent(session_id, action, language)
        return jsonify(_attach_session(response, session_id, language))

    if not message and not action:
        response = build_main_menu_response(language)
        return jsonify(_attach_session(response, session_id, language))

    if action.startswith("faq:"):
        response = handle_faq(action, language)
        return jsonify(_attach_session(response, session_id, language))

    if action.startswith("division_select:"):
        response = _handle_division_selection(session_id, action, language)
        return jsonify(_attach_session(response, session_id, language))

    if action in ("get_documents", "check_company", "loan_from_bank", "view_pricing"):
        lock_response = _maybe_lock_flow_action(session_id, action, language)
        if lock_response:
            return jsonify(_attach_session(lock_response, session_id, language))
        response = _run_flow_action(session_id, message, action, language)
        return jsonify(_attach_session(response, session_id, language))

    lock_response = _maybe_lock_active_flow(session_id, message, language)
    if lock_response:
        return jsonify(_attach_session(lock_response, session_id, language))

    flow = get_state(session_id).get("flow", "idle")
    division_for_flow = FLOW_STATE_TO_DIVISION.get(flow)
    if flow in ("documents", "company", "loan") and detected_intent and detected_intent.get("kind") not in ("flow", "suggestion"):
        response = _handle_detected_intent(session_id, detected_intent, language, division)
        if response:
            return jsonify(_attach_session(response, session_id, language))
    if flow in ("documents", "company", "loan"):
        if division_for_flow and division and division_for_flow != division:
            update_state(session_id, {"flow": "idle", "step": None, "context": {}, "pending_intent": None})
            flow = "idle"
    if flow == "documents":
        response = handle_document_flow(session_id, message, action, language)
        return jsonify(_attach_session(response, session_id, language))
    if flow == "company":
        response = handle_company_flow(session_id, message, action, language)
        return jsonify(_attach_session(response, session_id, language))
    if flow == "loan":
        response = handle_loan_flow(session_id, message, action, language)
        return jsonify(_attach_session(response, session_id, language))

    if message:
        response = _handle_detected_intent(session_id, detected_intent, language, division)
        if not response and division:
            response = _build_division_response(session_id, language, division)
        if response:
            return jsonify(_attach_session(response, session_id, language))
        update_state(session_id, {"pending_intent": None})
        response = handle_llm_message(message, language)
        return jsonify(_attach_session(response, session_id, language))

    response = build_main_menu_response(language)
    return jsonify(_attach_session(response, session_id, language))
