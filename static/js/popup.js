window.attachPopupListeners = function() {
  // Skip if we're on the chronology page
  if (window.location.pathname === "/chron") {
    return;
  }
  
  // Select all table cells but skip the chronology table
  const cells = document.querySelectorAll("td:not(#chronTable td)");
  cells.forEach(function(cell) {
    cell.removeEventListener("click", cellClickHandler);
    cell.addEventListener("click", cellClickHandler);
  });
};

function cellClickHandler(event) {
  // Skip if the cell is part of the chronology table
  if (event.target.closest('#chronTable')) {
    return;
  }
  
  const popup = document.getElementById("popup");
  const popupContent = document.getElementById("popupContent");
  const rect = this.getBoundingClientRect();

  // Default content: show cell text
  let contentHTML = `<p>${this.textContent}</p>`;
  
  // Check if this cell is a DateCell via assigned data attributes
  if (this.dataset.cellType === "date") {
    // Append an ACD checkbox reflecting the current acd value
    const checked = this.dataset.acd === "1" ? "checked" : "";
    contentHTML += `
      <label style="display:block; margin-top:10px;">
        <input type="checkbox" id="acdCheckbox" ${checked}> ACD
      </label>`;
  }
  
  popupContent.innerHTML = contentHTML;
  
  // Position the popup
  let popupLeft = rect.right + window.scrollX + 10;
  if (popupLeft + popup.offsetWidth > window.innerWidth) {
    popupLeft = rect.left + window.scrollX - popup.offsetWidth - 10;
  }
  popup.style.left = `${popupLeft}px`;
  popup.style.top = `${rect.bottom + window.scrollY + 10}px`;
  popup.style.display = "block";
  
  // For DateCell, attach listener to checkbox to update ACD value via AJAX.
  if (this.dataset.cellType === "date") {
    const acdCheckbox = document.getElementById("acdCheckbox");
    const cellId = this.dataset.cellId;
    acdCheckbox.addEventListener("change", function() {
      const newValue = acdCheckbox.checked ? 1 : 0;
      fetch("/update_datecell_acd", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({cell_id: cellId, acd: newValue})
      })
      .then(response => response.json())
      .then(data => {
        if(data.error) {
          console.error(data.error);
        } else {
          // Update the cell's dataset
          const cell = document.querySelector(`td[data-cell-id="${cellId}"]`);
          if(cell) {
            cell.dataset.acd = newValue;
            // Update row style inline for immediate feedback
            const row = cell.closest("tr");
            if(newValue == 1) {
              row.style.backgroundColor = "#ffcccc";
            } else {
              row.style.backgroundColor = "";
            }
          }
        }
      })
      .catch(err => {
        console.error(err);
      });
    });
  }
}

document.addEventListener("DOMContentLoaded", function() {
  // Skip popup initialization on the chronology page
  if (window.location.pathname !== "/chron") {
    attachPopupListeners();
    
    // Reattach after table changes using MutationObserver
    const tableContainer = document.querySelector(".table-container");
    if (tableContainer) {
      const observer = new MutationObserver(function(mutations, observer) {
        attachPopupListeners();
      });
      observer.observe(tableContainer, { childList: true, subtree: true });
    }
  }
});

// Add a global keydown listener to close the popup when Esc is pressed
document.addEventListener("keydown", function(event) {
  if (event.key === "Escape") {
    closePopup();
  }
});

function closePopup() {
  document.getElementById("popup").style.display = "none";
}
window.closePopup = closePopup;