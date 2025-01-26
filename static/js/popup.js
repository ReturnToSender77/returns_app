// Make attachPopupListeners globally available
window.attachPopupListeners = function() {
  const cells = document.querySelectorAll("td");
  cells.forEach(function(cell) {
    cell.addEventListener("click", function(event) {
      const popup = document.getElementById("popup");
      const rect = cell.getBoundingClientRect();

      // Position the popup near the clicked cell
      let popupLeft = rect.right + window.scrollX + 10;
      if (popupLeft + popup.offsetWidth > window.innerWidth) {
        popupLeft = rect.left + window.scrollX - popup.offsetWidth - 10;
      }
      popup.style.left = `${popupLeft}px`;
      popup.style.top = `${rect.bottom + window.scrollY + 10}px`;
      popup.style.display = "block";
    });
  });
};

document.addEventListener("DOMContentLoaded", function() {
  // Initial call to add listeners to existing cells
  attachPopupListeners();

  // Observe changes in the table to add listeners to new cells
  const observer = new MutationObserver(attachPopupListeners);
  const tableContainer = document.querySelector(".table-container");
  if (tableContainer) {
    observer.observe(tableContainer, { childList: true, subtree: true });
  }

  // Close popup function
  window.closePopup = function() {
    document.getElementById("popup").style.display = "none";
  };
});