// Enhanced popup for chronology page with footnote support - restricted to Chron Table only

// Global storage for footnotes
const footnotes = {};
let currentTableId = null;
let currentElementId = null;

// Initialize footnote system
function initFootnoteSystem() {
  console.log('Initializing footnote system - Chron Table only');
  
  // Load existing footnotes if we have a table ID
  if (currentTableId) {
    loadFootnotes(currentTableId);
  }
  
  // Attach click listeners to table headers and cells in the returns table for column adding only
  document.querySelectorAll('#chronTable thead th').forEach((th, index) => {
    th.addEventListener('click', function(event) {
      event.preventDefault();
      // Show column adding option only (no footnote functionality)
      showColumnAddPopup(event, index, this.textContent);
    });
  });

  // For returns table cells, just prevent default behavior
  attachReturnsCellListeners();
  
  // Initialize the Chron table popups with full footnote functionality
  initChronTablePopups();
}

// Load footnotes from the server - only for Chron Table
function loadFootnotes(tableId) {
  console.log(`Loading footnotes for table ${tableId}`);
  
  fetch(`/get_footnotes/${tableId}`)
    .then(response => response.json())
    .then(data => {
      if (data.success && data.footnotes) {
        // Clear existing footnotes
        Object.keys(footnotes).forEach(key => delete footnotes[key]);
        
        // Load new footnotes - only chron table ones
        Object.entries(data.footnotes).forEach(([key, value]) => {
          // Only load footnotes for the chron table
          if (key.startsWith('chron_')) {
            footnotes[key] = value;
          }
        });
        
        console.log(`Loaded ${Object.keys(footnotes).length} chron table footnotes`);
        
        // Update indicators
        updateFootnoteIndicators();
      } else if (data.error) {
        console.error(`Error loading footnotes: ${data.error}`);
      }
    })
    .catch(error => {
      console.error(`Error loading footnotes: ${error}`);
    });
}

// Column Add popup for Returns Table headers - no footnote functionality
function showColumnAddPopup(event, columnIndex, headerText) {
  event.stopPropagation();
  
  // Create or get the popup
  let popup = document.getElementById('footnotePopup');
  if (!popup) {
    popup = document.createElement('div');
    popup.id = 'footnotePopup';
    popup.className = 'footnote-popup';
    document.body.appendChild(popup);
  }
  
  // Set content - only for column adding, no footnote options
  popup.innerHTML = `
    <div class="footnote-header">
      <h3>Column Actions - Returns Table</h3>
      <button class="close-button" onclick="closeFootnotePopup()">×</button>
    </div>
    <div class="footnote-content">
      <p><strong>Column:</strong> ${headerText}</p>
      <button class="btn btn-primary mb-2" onclick="addColumnToChron(${columnIndex})">Add Column to Chron Table</button>
      <div class="footnote-actions mt-3">
        <button class="btn btn-secondary" onclick="closeFootnotePopup()">Cancel</button>
      </div>
    </div>
  `;

  // Position and show the popup
  popup.style.display = 'block';
  
  // Position near the clicked element
  const rect = event.target.getBoundingClientRect();
  popup.style.top = (rect.bottom + window.scrollY + 10) + 'px';
  popup.style.left = (rect.left + window.scrollX) + 'px';
}

// Initialize popups for the Chron table
function initChronTablePopups() {
  console.log('Initializing Chron table popups with footnote support');
  
  // Attach click listeners to Chron table headers
  document.querySelectorAll('#customChronTable thead th.column-header').forEach((th, index) => {
    // Don't re-attach if already has listener
    if (th.hasFootnoteListener) return;
    
    th.hasFootnoteListener = true;
    th.addEventListener('click', function(event) {
      // Don't show popup if clicking on the remove button or handle
      if (event.target.classList.contains('column-remove-btn') || 
          event.target.closest('.column-remove-btn') ||
          event.target.classList.contains('col-handle') ||
          event.target.closest('.col-handle')) {
        return;
      }
      
      event.preventDefault();
      event.stopPropagation();
      
      // Get the actual column index from the data attribute
      const columnIndex = parseInt(this.getAttribute('data-column-index'), 10);
      if (isNaN(columnIndex)) return;
      
      // Show footnote popup for chron table headers
      showFootnotePopup(`chron_header_${columnIndex}`, this.textContent.trim(), true, 'chron');
    });
  });
  
  // Attach listeners to Chron table cells
  attachChronCellListeners();
}

// Attach listeners to returns table cells - no footnote functionality
function attachReturnsCellListeners() {
  document.querySelectorAll('#chronTable tbody tr').forEach((tr) => {
    tr.querySelectorAll('td').forEach((td) => {
      td.addEventListener('click', function(event) {
        // Just prevent default behavior, no popup
        event.preventDefault();
      });
    });
  });
}

// Attach listeners to Chron table cells with full footnote functionality
function attachChronCellListeners() {
  document.querySelectorAll('#customChronTable tbody tr').forEach((tr, rowIndex) => {
    tr.querySelectorAll('td').forEach((td, colIndex) => {
      td.addEventListener('click', function(event) {
        event.preventDefault();
        showFootnotePopup(`chron_cell_${rowIndex}_${colIndex}`, this.textContent, false, 'chron');
      });
    });
  });
}

// Show footnote popup - only used for Chron Table now
function showFootnotePopup(elementId, content, isHeader = false, tableType = 'chron') {
  currentElementId = elementId;
  
  // Create or get the footnote popup
  let popup = document.getElementById('footnotePopup');
  if (!popup) {
    popup = document.createElement('div');
    popup.id = 'footnotePopup';
    popup.className = 'footnote-popup';
    document.body.appendChild(popup);
  }

  // Get existing footnote if any
  const existingFootnote = footnotes[elementId] || '';
  
  // Set content
  popup.innerHTML = `
    <div class="footnote-header">
      <h3>${isHeader ? 'Column Header' : 'Cell'} Footnote - Chron Table</h3>
      <button class="close-button" onclick="closeFootnotePopup()">×</button>
    </div>
    <div class="footnote-content">
      <p><strong>Content:</strong> ${content}</p>
      <div class="form-group">
        <label for="footnoteText">Footnote:</label>
        <textarea id="footnoteText" rows="3" class="form-control">${existingFootnote}</textarea>
      </div>
      <div class="footnote-actions">
        <button class="btn btn-primary" onclick="saveFootnote()">Save</button>
        <button class="btn btn-secondary" onclick="closeFootnotePopup()">Cancel</button>
      </div>
    </div>
  `;

  // Position and show the popup
  popup.style.display = 'block';
  
  // Center the popup
  popup.style.top = '50%';
  popup.style.left = '50%';
  popup.style.transform = 'translate(-50%, -50%)';
  
  // Focus the textarea
  document.getElementById('footnoteText').focus();
}

// Save the footnote - now simpler with Chron Table only
function saveFootnote() {
  if (!currentElementId) return;
  
  const footnoteText = document.getElementById('footnoteText').value.trim();
  
  // Check if it's a change (save network requests)
  const currentFootnote = footnotes[currentElementId] || '';
  if (currentFootnote === footnoteText) {
    closeFootnotePopup();
    return;
  }
  
  // Update local storage
  footnotes[currentElementId] = footnoteText;
  
  // Save to server
  if (currentTableId) {
    fetch('/save_footnote', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        element_id: currentElementId,
        footnote: footnoteText,
        table_id: currentTableId
      }),
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        console.error(`Error saving footnote: ${data.error}`);
      } else {
        console.log(`Footnote ${data.action} successfully`);
      }
    })
    .catch(error => {
      console.error('Error saving footnote:', error);
    });
  }
  
  // Add visual indicator if footnote exists
  updateFootnoteIndicators();
  
  // Close the popup
  closeFootnotePopup();
}

// Add column to chron table - delegates to the function in chron_tables.js
function addColumnToChron(columnIndex) {
  console.log('Adding column to chron table:', columnIndex);
  
  // Call the function in chron_tables.js
  if (window.addColumnToChronTable) {
    window.addColumnToChronTable(columnIndex);
  } else {
    console.error("Could not find addColumnToChronTable function");
  }
  
  closeFootnotePopup();
}

// Update visual indicators for elements with footnotes - only in Chron Table
function updateFootnoteIndicators() {
  // Clear existing indicators
  document.querySelectorAll('.footnote-indicator').forEach(el => el.remove());
  
  // Add indicators for headers in chron table
  document.querySelectorAll('#customChronTable thead th').forEach((th, index) => {
    const headerId = `chron_header_${index}`;
    if (footnotes[headerId]) {
      const indicator = document.createElement('sup');
      indicator.className = 'footnote-indicator';
      indicator.textContent = '*';
      indicator.title = footnotes[headerId];
      // Append to the content part, not to the handle or remove button
      th.appendChild(indicator);
    }
  });
  
  // Add indicators for cells in chron table
  document.querySelectorAll('#customChronTable tbody tr').forEach((tr, rowIndex) => {
    tr.querySelectorAll('td').forEach((td, colIndex) => {
      const cellId = `chron_cell_${rowIndex}_${colIndex}`;
      if (footnotes[cellId]) {
        const indicator = document.createElement('sup');
        indicator.className = 'footnote-indicator';
        indicator.textContent = '*';
        indicator.title = footnotes[cellId];
        td.appendChild(indicator);
      }
    });
  });
}

// Close the footnote popup
function closeFootnotePopup() {
  const popup = document.getElementById('footnotePopup');
  if (popup) {
    popup.style.display = 'none';
  }
  currentElementId = null;
}

// Update Chron table popups whenever the Chron table changes
function updateChronTablePopups() {
  // Delay slightly to ensure DOM is updated
  setTimeout(() => {
    initChronTablePopups();
  }, 100);
}

// Make functions globally available
window.showFootnotePopup = showFootnotePopup;
window.closeFootnotePopup = closeFootnotePopup;
window.saveFootnote = saveFootnote;
window.initFootnoteSystem = initFootnoteSystem;
window.attachReturnsCellListeners = attachReturnsCellListeners;
window.attachChronCellListeners = attachChronCellListeners;
window.updateChronTablePopups = updateChronTablePopups;
window.getFootnotes = function() { return footnotes; };
window.setCurrentTableId = function(id) { currentTableId = id; };
window.addColumnToChron = addColumnToChron;
window.showColumnAddPopup = showColumnAddPopup;
