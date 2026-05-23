const checkoutItems = document.getElementById("checkout-items");
const checkoutSubtotal = document.getElementById("checkout-subtotal");
const checkoutFee = document.getElementById("checkout-fee");
const checkoutTotal = document.getElementById("checkout-total");
const checkoutCartCount = document.getElementById("checkout-cart-count");
const checkoutPay = document.getElementById("checkout-pay");
const checkoutContinue = document.getElementById("checkout-continue");
const checkoutBack = document.getElementById("checkout-back");
const checkoutSuccess = document.getElementById("checkout-success");
const checkoutReturn = document.getElementById("checkout-return");

const getStoredCart = () => {
  try {
    const stored = localStorage.getItem("ssm_cart");
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    return [];
  }
};

const saveStoredCart = (cart) => {
  localStorage.setItem("ssm_cart", JSON.stringify(cart));
};

const normalizePrice = (priceText) => {
  if (!priceText) return 0;
  const value = priceText.toString().replace(/[^0-9.]/g, "");
  return Number.parseFloat(value || "0");
};

const renderCheckout = () => {
  const cart = getStoredCart();
  checkoutItems.innerHTML = "";

  if (!cart.length) {
    checkoutItems.innerHTML = `<div class="checkout-empty">Your cart is empty.</div>`;
    checkoutSubtotal.innerText = "RM 0";
    checkoutFee.innerText = "RM 0";
    checkoutTotal.innerText = "RM 0";
    checkoutCartCount.innerText = "0";
    return;
  }

  let subtotal = 0;

  cart.forEach((item) => {
    const row = document.createElement("div");
    row.className = "checkout-row";

    const details = document.createElement("div");
    details.className = "checkout-details";
    details.innerHTML = `<h4>${item.title}</h4><p>${item.note || "Premium verification ready"}</p>`;

    const price = document.createElement("div");
    price.className = "checkout-price";
    const non = normalizePrice(item.pricing?.non_ctc);
    const ctc = normalizePrice(item.pricing?.ctc);
    const best = Math.max(non, ctc);
    subtotal += best * item.qty;
    price.innerHTML = `<span>${item.pricing?.non_ctc || "RM 0"}</span><span>${item.pricing?.ctc || "RM 0"}</span>`;

    const remove = document.createElement("button");
    remove.className = "ghost";
    remove.innerText = "Remove";
    remove.addEventListener("click", () => {
      const updated = cart.filter((cartItem) => cartItem.documentId !== item.documentId);
      saveStoredCart(updated);
      renderCheckout();
    });

    row.appendChild(details);
    row.appendChild(price);
    row.appendChild(remove);
    checkoutItems.appendChild(row);
  });

  const fee = subtotal * 0.03;
  const total = subtotal + fee;
  checkoutSubtotal.innerText = `RM ${subtotal.toFixed(2)}`;
  checkoutFee.innerText = `RM ${fee.toFixed(2)}`;
  checkoutTotal.innerText = `RM ${total.toFixed(2)}`;
  checkoutCartCount.innerText = `${cart.length}`;
};

const continueBrowsing = () => {
  window.location.href = "/";
};

checkoutPay?.addEventListener("click", () => {
  checkoutSuccess.classList.add("active");
  saveStoredCart([]);
});

checkoutContinue?.addEventListener("click", continueBrowsing);
checkoutBack?.addEventListener("click", continueBrowsing);
checkoutReturn?.addEventListener("click", continueBrowsing);

renderCheckout();
