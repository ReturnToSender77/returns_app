document.addEventListener("DOMContentLoaded", function () {
    const popup = document.getElementById("popup");

    function addCellClickListeners() {
      const tableCells = document.querySelectorAll("td");
      tableCells.forEach(function (cell) {
        cell.addEventListener("click", function (event) {
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
    }

    // Initial call to add listeners to existing cells
    addCellClickListeners();

    // Observe changes in the table to add listeners to new cells
    const observer = new MutationObserver(addCellClickListeners);
    const tableContainer = document.querySelector(".table-container");
    if (tableContainer) {
      observer.observe(tableContainer, { childList: true, subtree: true });
    }

    // Close popup function
    window.closePopup = function () {
      popup.style.display = "none";
    };
  });