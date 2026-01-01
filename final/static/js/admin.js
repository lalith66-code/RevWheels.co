document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".delete-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      if (!confirm("Delete this product?")) {
        e.preventDefault();
      }
    });
  });
});
