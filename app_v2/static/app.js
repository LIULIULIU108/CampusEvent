document.addEventListener("submit", function (event) {
  const form = event.target;
  if (!(form instanceof HTMLFormElement)) return;
  const message = form.getAttribute("data-confirm");
  if (message && !window.confirm(message)) {
    event.preventDefault();
  }
});

document.querySelectorAll("[data-dismiss]").forEach(function (button) {
  button.addEventListener("click", function () {
    const alert = button.closest(".alert");
    if (alert) alert.remove();
  });
});
