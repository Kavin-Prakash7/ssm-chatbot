
const chatToggle = document.getElementById("chat-toggle");
const chatPanel = document.getElementById("chatbot");
const chatCollapse = document.getElementById("chat-collapse");
const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");
const chatMessages = document.getElementById("chat-messages");
const chatBody = document.querySelector(".chatbot-window");
const miniCart = document.getElementById("mini-cart");
const cartPanel = document.getElementById("cart-panel");
const cartClose = document.getElementById("cart-close");
const cartItems = document.getElementById("cart-items");
const cartCount = document.getElementById("cart-count");
const navCartCount = document.getElementById("nav-cart-count");
const navCart = document.querySelector(".nav-cart");
const chatbotCartButton = document.getElementById("chatbot-cart-button");
const chatbotCartCount = document.getElementById("chatbot-cart-count");
const chatbotCartTotal = document.getElementById("chatbot-cart-total");
const chatScrollTopBtn = document.getElementById("chat-scroll-top");
const cartTotalPreview = document.getElementById("cart-total-preview");
const cartPreview = document.getElementById("cart-preview");
const cartTotalNon = document.getElementById("cart-total-non");
const cartTotalCtc = document.getElementById("cart-total-ctc");
const cartContinue = document.getElementById("cart-continue");
const cartCheckout = document.getElementById("cart-checkout");
const toastContainer = document.getElementById("toast-container");
const heroSearchInput = document.getElementById("hero-search-input");
const heroSearchBtn = document.getElementById("hero-search-btn");
const smartSearchInput = document.getElementById("smart-search-input");
const smartSearchBtn = document.getElementById("smart-search-btn");
const smartSuggestionPanel = document.getElementById("smart-suggestion-panel");
const smartSearchSuggestions = document.getElementById("smart-search-suggestions");
const heroOpenAssistant = document.getElementById("hero-open-assistant");
const ctaStartAssistant = document.getElementById("cta-start-assistant");
const ctaExploreDocs = document.getElementById("cta-explore-docs");

const state = {
  sessionId: null,
  language: "en",
  cart: [],
  cardLookup: {},
};

const handleScrollTopVisibility = () => {
  if (!chatScrollTopBtn) return;
  if (chatMessages.scrollTop > 180) {
    chatScrollTopBtn.classList.add("visible");
  } else {
    chatScrollTopBtn.classList.remove("visible");
  }
};

chatScrollTopBtn?.addEventListener("click", () => {
  chatMessages.scrollTo({ top: 0, behavior: "smooth" });
});

chatMessages?.addEventListener("scroll", handleScrollTopVisibility);
handleScrollTopVisibility();

let pendingRequests = 0;
let loadingGroup = null;
let hasRenderedResponse = false;

const loadStoredCart = () => {
  try {
    const stored = localStorage.getItem("ssm_cart");
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    return [];
  }
};

state.cart = loadStoredCart();

const toggleChat = () => {
  chatPanel.classList.toggle("active");
  if (!chatPanel.classList.contains("active")) {
    cartPanel?.classList.remove("active");
  }
};

const toggleCart = () => {
  cartPanel.classList.toggle("active");
};

miniCart?.addEventListener("click", toggleCart);
chatbotCartButton?.addEventListener("click", toggleCart);
cartClose?.addEventListener("click", toggleCart);
cartContinue?.addEventListener("click", () => {
  cartPanel?.classList.remove("active");
  if (!chatPanel.classList.contains("active")) {
    chatPanel.classList.add("active");
  }
});
cartCheckout?.addEventListener("click", () => {
  handleCheckoutAttempt();
});

chatToggle.addEventListener("click", toggleChat);
chatCollapse.addEventListener("click", toggleChat);
navCart?.addEventListener("click", (event) => {
  event.preventDefault();
  window.location.href = "/checkout";
});

const isNearBottom = () => {
  const threshold = 120;
  const scrollable = chatMessages.scrollHeight - chatMessages.clientHeight;
  if (scrollable <= 4) return false;
  return scrollable - chatMessages.scrollTop < threshold;
};

const scrollToBottom = (force = false) => {
  if (!force && !isNearBottom()) return;
  chatMessages.scrollTo({
    top: chatMessages.scrollHeight,
    behavior: "smooth",
  });
};

const createResponseGroup = () => {
  const group = document.createElement("div");
  group.className = "response-group";
  chatMessages.appendChild(group);
  return group;
};

const addBubble = (text, type = "bot", container = chatMessages) => {
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${type}`;
  bubble.innerText = text;
  container.appendChild(bubble);
  // Only force scroll for user bubbles; bot bubbles rely on renderResponse logic
  scrollToBottom(type === "user");
};

const addTitle = (title, container = chatMessages) => {
  if (!title) return;
  const titleEl = document.createElement("div");
  titleEl.className = "chat-title";
  titleEl.innerText = title;
  container.appendChild(titleEl);
};

const addActionRow = (buttons, className = "action-row", container = chatMessages) => {
  if (!buttons || !buttons.length) return;
  const row = document.createElement("div");
  row.className = className;
  buttons.forEach((btn) => {
    const button = document.createElement("button");
    button.innerText = btn.label;
    if (btn.style) {
      button.classList.add(btn.style);
    }
    if (btn.style === "chip") {
      button.classList.add("chip");
    }
    button.addEventListener("click", () => {
      if (btn.id.startsWith("preview:")) {
        openPdfPreview(btn.id);
      }
      if (btn.id.startsWith("add_to_cart:")) {
        addToCartFromAction(btn.id);
      }
      sendAction(btn.id, btn.label);
    });
    row.appendChild(button);
  });
  container.appendChild(row);
};

const normalizePrice = (priceText) => {
  if (!priceText) return 0;
  const value = priceText.toString().replace(/[^0-9.]/g, "");
  return Number.parseFloat(value || "0");
};

const cacheCardData = (cards) => {
  cards.forEach((card) => {
    if (!card.id) return;
    state.cardLookup[card.id] = {
      title: card.title,
      pricing: card.pricing || { non_ctc: "RM 0", ctc: "RM 0" },
      note: card.meta?.note || "",
    };
  });
};

const persistCart = () => {
  localStorage.setItem("ssm_cart", JSON.stringify(state.cart));
};

const showToast = (message) => {
  if (!toastContainer) return;
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.innerText = message;
  toastContainer.appendChild(toast);
  setTimeout(() => toast.remove(), 2800);
};

const openAssistant = () => {
  if (!chatPanel.classList.contains("active")) {
    chatPanel.classList.add("active");
  }
};

const openPdfPreview = (actionId) => {
  const parts = actionId.split(":");
  if (parts.length < 3) return;
  const docId = parts[1];
  const variant = parts[2];
  const filename = `${docId}_${variant}.pdf`;
  fetch(`/sample-pdf/${filename}`, { method: "HEAD" })
    .then((response) => {
      if (response.ok) {
        window.open(`/sample-pdf/${filename}`, "_blank");
      } else {
        window.open(`/sample-pdf/${filename}.pdf`, "_blank");
      }
    })
    .catch(() => {
      window.open(`/sample-pdf/${filename}`, "_blank");
    });
};

const handleCheckoutAttempt = () => {
  if (!state.cart.length) {
    openAssistant();
    showToast(
      state.language === "en"
        ? "Your cart is empty. Add documents to continue."
        : "Troli anda kosong. Sila tambah dokumen dahulu."
    );
    addBubble(
      state.language === "en"
        ? "🛒 Your cart is empty. Add documents first."
        : "🛒 Troli anda kosong. Sila tambah dokumen dahulu.",
      "bot"
    );
    return;
  }
  persistCart();
  window.location.href = "/checkout";
};

const showCartGlow = () => {
  if (!chatbotCartButton) return;
  chatbotCartButton.classList.add("glow-ring");
  setTimeout(() => chatbotCartButton.classList.remove("glow-ring"), 900);
};

const showCartConfirmation = (message) => {
  if (!chatBody) return;
  const confirmation = document.createElement("div");
  confirmation.className = "cart-float-confirmation";
  confirmation.innerText = message;
  chatBody.appendChild(confirmation);
  requestAnimationFrame(() => confirmation.classList.add("visible"));
  setTimeout(() => confirmation.classList.remove("visible"), 1100);
  setTimeout(() => confirmation.remove(), 1500);
};

const addToCartFromAction = (actionId, card = null) => {
  const docId = actionId.split(":")[1];
  const existing = state.cart.find((item) => item.documentId === docId);
  if (existing) {
    existing.qty += 1;
  } else {
    const cached = state.cardLookup[docId] || {};
    const source = card
      ? {
          title: card.title,
          pricing: card.pricing || { non_ctc: "RM 0", ctc: "RM 0" },
          note: card.meta?.note || "",
        }
      : cached;
    state.cart.push({
      documentId: docId,
      title: source.title || docId.replace(/_/g, " "),
      pricing: source.pricing || { non_ctc: "RM 0", ctc: "RM 0" },
      note: source.note || "",
      qty: 1,
    });
  }
  if (chatbotCartButton) {
    chatbotCartButton.classList.add("pulse");
    setTimeout(() => chatbotCartButton.classList.remove("pulse"), 600);
  }
  if (miniCart) {
    miniCart.classList.add("pulse");
    setTimeout(() => miniCart.classList.remove("pulse"), 600);
  }
  showCartGlow();
  showToast(
    state.language === "en"
      ? `✅ ${existing ? existing.title : state.cardLookup[docId]?.title || "Document"} added to cart`
      : `✅ ${existing ? existing.title : state.cardLookup[docId]?.title || "Dokumen"} ditambah ke troli`
  );
  showCartConfirmation(
    state.language === "en"
      ? `${state.cardLookup[docId]?.title || "Document"} added`
      : `${state.cardLookup[docId]?.title || "Dokumen"} ditambah`
  );
  renderCart();
};

const removeCartItem = (documentId) => {
  state.cart = state.cart.filter((item) => item.documentId !== documentId);
  renderCart();
};

const renderCart = () => {
  if (!cartItems) return;
  cartItems.innerHTML = "";
  const totalItems = state.cart.reduce((sum, item) => sum + item.qty, 0);
  if (cartCount) {
    cartCount.innerText = totalItems;
  }
  if (navCartCount) {
    navCartCount.innerText = totalItems;
  }
  if (chatbotCartCount) {
    chatbotCartCount.innerText = totalItems;
  }

  if (!state.cart.length) {
    const empty = document.createElement("div");
    empty.className = "cart-empty";
    empty.innerText =
      state.language === "en"
        ? "Your cart is empty. Add documents to prepare checkout."
        : "Troli anda kosong. Tambah dokumen untuk persediaan pembayaran.";
    cartItems.appendChild(empty);
    cartTotalNon.innerText = "RM 0";
    cartTotalCtc.innerText = "RM 0";
    if (cartTotalPreview) {
      cartTotalPreview.innerText = "RM 0";
    }
    if (chatbotCartTotal) {
      chatbotCartTotal.innerText = "RM 0";
    }
    persistCart();
    return;
  }

  let totalNon = 0;
  let totalCtc = 0;

  state.cart.forEach((item) => {
    const wrapper = document.createElement("div");
    wrapper.className = "cart-item";

    const title = document.createElement("h4");
    title.innerText = item.title;
    wrapper.appendChild(title);

    if (item.note) {
      const note = document.createElement("p");
      note.innerText = item.note;
      wrapper.appendChild(note);
    }

    const prices = document.createElement("div");
    prices.className = "price-row";
    prices.innerHTML = `<span>Non-CTC: ${item.pricing.non_ctc}</span><span>CTC: ${item.pricing.ctc}</span>`;
    wrapper.appendChild(prices);

    const removeBtn = document.createElement("button");
    removeBtn.innerText = state.language === "en" ? "Remove" : "Buang";
    removeBtn.addEventListener("click", () => removeCartItem(item.documentId));
    wrapper.appendChild(removeBtn);

    cartItems.appendChild(wrapper);

    totalNon += normalizePrice(item.pricing.non_ctc) * item.qty;
    totalCtc += normalizePrice(item.pricing.ctc) * item.qty;
  });

  cartTotalNon.innerText = `RM ${totalNon.toFixed(2)}`;
  cartTotalCtc.innerText = `RM ${totalCtc.toFixed(2)}`;
  if (cartTotalPreview) {
    cartTotalPreview.innerText = `RM ${totalNon.toFixed(2)}`;
  }
  if (chatbotCartTotal) {
    chatbotCartTotal.innerText = `RM ${totalNon.toFixed(2)}`;
  }
  persistCart();
};

const addCards = (cards, container = chatMessages) => {
  if (!cards || !cards.length) return;
  const grid = document.createElement("div");
  grid.className = "card-grid";
  cards.forEach((card) => {
    const wrapper = document.createElement("div");
    wrapper.className = "info-card";

    const header = document.createElement("div");
    header.className = "card-header";

    const title = document.createElement("h4");
    title.innerText = card.title;
    header.appendChild(title);

    if (card.pricing) {
      const badges = document.createElement("div");
      badges.className = "badge-row";
      const nonCtc = document.createElement("span");
      nonCtc.className = "badge";
      nonCtc.innerText = `Non-CTC ${card.pricing.non_ctc || "-"}`;
      const ctc = document.createElement("span");
      ctc.className = "badge";
      ctc.innerText = `CTC ${card.pricing.ctc || "-"}`;
      badges.appendChild(nonCtc);
      badges.appendChild(ctc);
      header.appendChild(badges);
    }

    wrapper.appendChild(header);

    if (card.subtitle) {
      const bestFor = document.createElement("div");
      bestFor.className = "card-meta";
      bestFor.innerHTML = `<span>Best for</span><strong>${card.subtitle}</strong>`;
      wrapper.appendChild(bestFor);
    }

    if (card.meta && card.meta.note) {
      const note = document.createElement("p");
      note.className = "card-note";
      note.innerText = `💡 ${card.meta.note}`;
      wrapper.appendChild(note);
    }

    if (card.actions && card.actions.length) {
      const actions = document.createElement("div");
      actions.className = "card-actions";
      card.actions.forEach((action) => {
        const button = document.createElement("button");
        button.innerText = action.label;
        if (action.style) {
          button.classList.add(action.style);
        }
        button.addEventListener("click", () => {
          if (action.id.startsWith("preview:")) {
            openPdfPreview(action.id);
          }
          if (action.id.startsWith("add_to_cart:")) {
            addToCartFromAction(action.id, card);
          }
          sendAction(action.id, action.label);
        });
        actions.appendChild(button);
      });
      const checkoutButton = document.createElement("button");
      checkoutButton.className = "ghost";
      checkoutButton.innerText = "Checkout";
      checkoutButton.addEventListener("click", handleCheckoutAttempt);
      actions.appendChild(checkoutButton);
      wrapper.appendChild(actions);
    }

    grid.appendChild(wrapper);
  });
  container.appendChild(grid);
};

const renderResponse = (payload) => {
  if (payload.cards && payload.cards.length) {
    cacheCardData(payload.cards);
  }
  const group = createResponseGroup();
  if (payload.title) {
    addTitle(payload.title, group);
  }
  if (payload.message) {
    addBubble(payload.message, "bot", group);
  }
  addActionRow(payload.buttons || [], "action-row", group);
  addCards(payload.cards || [], group);
  if (payload.suggestions && payload.suggestions.length) {
    addActionRow(payload.suggestions, "chip-row", group);
  }
  // Do not auto-scroll the very first response group to the bottom;
  // keep greeting / quick actions visible at the top.
  if (hasRenderedResponse) {
    scrollToBottom();
  } else {
    chatMessages.scrollTop = 0;
    hasRenderedResponse = true;
  }
};

const showPending = () => {
  if (loadingGroup) return;
  loadingGroup = document.createElement("div");
  loadingGroup.className = "response-group loading";

  const shimmer = document.createElement("div");
  shimmer.className = "loading-stack";
  shimmer.innerHTML = `
    <div class="loading-shimmer w-90"></div>
    <div class="loading-shimmer w-70"></div>
    <div class="loading-shimmer w-50"></div>
  `;

  const typing = document.createElement("div");
  typing.className = "typing-indicator";
  typing.innerHTML = "<span></span><span></span><span></span>";

  loadingGroup.appendChild(shimmer);
  loadingGroup.appendChild(typing);
  chatMessages.appendChild(loadingGroup);
};

const hidePending = () => {
  if (!loadingGroup) return;
  loadingGroup.remove();
  loadingGroup = null;
};

const sendPayload = async (payload) => {
  pendingRequests += 1;
  showPending();
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: state.sessionId,
      ...payload,
    }),
  });
  const data = await response.json();
  pendingRequests = Math.max(0, pendingRequests - 1);
  if (pendingRequests === 0) {
    hidePending();
  }
  state.sessionId = data.data?.session_id || state.sessionId;
  state.language = data.data?.language || state.language;
  renderCart();
  renderResponse(data);
};

const sendMessage = () => {
  const text = chatInput.value.trim();
  if (!text) return;
  addBubble(text, "user");
  chatInput.value = "";
  sendPayload({ message: text });
};

const sendAction = (actionId, label) => {
  if (label) {
    addBubble(label, "user");
  }
  if (actionId && actionId.startsWith("purpose:")) {
    showPending();
  }
  sendPayload({ action: actionId });
};

const sendSearchMessage = (text) => {
  if (!text) return;
  openAssistant();
  addBubble(text, "user");
  sendPayload({ message: text });
};

const renderSmartSuggestions = (value) => {
  if (!smartSuggestionPanel) return;
  smartSuggestionPanel.innerHTML = "";
  if (!value || value.length < 2) return;
  const suggestions = [
    `${value} company profile`,
    `${value} business verification`,
    `${value} bank documents`,
  ];
  suggestions.forEach((suggestion) => {
    const item = document.createElement("div");
    item.className = "suggestion-item";
    item.innerText = suggestion;
    item.addEventListener("click", () => sendSearchMessage(suggestion));
    smartSuggestionPanel.appendChild(item);
  });
};

chatSend.addEventListener("click", sendMessage);
chatInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    sendMessage();
  }
});

heroSearchBtn?.addEventListener("click", () => {
  sendSearchMessage(heroSearchInput?.value.trim());
});

heroSearchInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    sendSearchMessage(heroSearchInput?.value.trim());
  }
});

smartSearchBtn?.addEventListener("click", () => {
  sendSearchMessage(smartSearchInput?.value.trim());
});

smartSearchInput?.addEventListener("input", (event) => {
  renderSmartSuggestions(event.target.value.trim());
});

smartSearchInput?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    sendSearchMessage(smartSearchInput?.value.trim());
  }
});

smartSearchSuggestions?.addEventListener("click", (event) => {
  const target = event.target.closest("button");
  if (!target) return;
  sendSearchMessage(target.dataset.query || target.innerText);
});

heroOpenAssistant?.addEventListener("click", openAssistant);
ctaStartAssistant?.addEventListener("click", openAssistant);
ctaExploreDocs?.addEventListener("click", () => {
  openAssistant();
  sendAction("get_documents", "Explore Documents");
});

window.addEventListener("load", () => {
  renderCart();
  sendPayload({ action: "main_menu" });
});
