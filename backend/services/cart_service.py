
from backend.utils.state_manager import get_state


def get_cart(session_id):
    state = get_state(session_id)
    return state.get("cart", [])
