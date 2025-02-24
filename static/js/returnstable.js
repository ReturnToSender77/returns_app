// Wait for the document to be fully loaded before initializing
$(document).ready(function() {
  const savedTableId = localStorage.getItem('selectedReturnsTable');
  
  // Only proceed if there's a saved table id and it's not the "upload" flag.
  if (savedTableId && savedTableId !== "upload") {
    // Try fetching the table data
    fetch(`/get_table/${savedTableId}`)
      .then(response => {
        // If the table does not exist, clean up the localStorage entry.
        if (!response.ok) {
          localStorage.removeItem('selectedReturnsTable');
          // Instead of throwing an error, simply resolve with an empty object.
          return {};
        }
        return response.json();
      })
      .then(data => {
        // Proceed only if table_html is present.
        if (data.table_html) {
          const container = document.querySelector('.table-container') || createTableContainer();
          container.innerHTML = data.table_html;
          initDataTable();
          document.getElementById('returnsTableSelect').value = savedTableId;
        }
      })
      .catch(error => {
        console.warn('No valid saved table found, localStorage cleared.');
      });
  } else if (document.querySelector('#returnsTable')) {
    initDataTable();
  }
  attachEventListeners();
});

/**
 * Initializes the DataTable plugin with custom options
 */
function initDataTable() {
  $('#returnsTable').DataTable({
    destroy: true,
    paging: false,            // One page only
    scrollY: "1200px",        // Set ReturnsTable height
    scrollCollapse: true,     
    searching: true,
    ordering: true,
    scrollX: true,
    dom: 'Bfrtip',
    buttons: ['copy', 'csv', 'excel', 'print'],
    info: false, // Hide default info
    rowCallback: function(row, data, index) {
      if ($(row).find("td[data-acd='1']").length > 0) {
        $(row).addClass('acd-row');
      }
    },
    initComplete: function(settings, json) {
      if (window.attachPopupListeners) {
        window.attachPopupListeners();
      }
      applyACDRowStyles();
      updateCustomFooter();
    },
    drawCallback: function(settings) {
      if (window.attachPopupListeners) {
        window.attachPopupListeners();
      }      
    }
  });
}

function updateCustomFooter() {
  const footerEl = document.getElementById('customFooter');
  if (!footerEl) return; // No footer defined
  const tableEl = document.getElementById('returnsTable');
  const tableName = tableEl ? tableEl.dataset.tableName || "Returns" : "Returns";
  let dates = [];
  $('#returnsTable tbody tr').each(function() {
    const cellText = $(this).find('td[data-cell-type="date"]').first().text();
    if (cellText) {
      let d = new Date(cellText);
      if (!isNaN(d.getTime())) {
        dates.push(d);
      }
    }
  });
  if (dates.length > 0) {
    const minDate = new Date(Math.min(...dates));
    const maxDate = new Date(Math.max(...dates));
    const formatDate = function(date) {
      const m = (date.getMonth() + 1).toString().padStart(2, '0');
      const d = date.getDate().toString().padStart(2, '0');
      return `${m}/${d}/${date.getFullYear()}`;
    };
    footerEl.innerText = `Showing ${tableName} returns from ${formatDate(minDate)} to ${formatDate(maxDate)}`;
  } else {
    footerEl.innerText = `Showing ${tableName} returns (no date data)`;
  }
}

/**
 * Attaches event listeners to the various elements on the page.
 */
function attachEventListeners() {
  const fileInput = document.getElementById('fileInput');
  // Remove any previous file upload handler before adding our new one.
  fileInput.removeEventListener('change', fileUploadHandler);
  fileInput.addEventListener('change', fileUploadHandler);

  document.getElementById('returnsTableSelect').addEventListener('change', function() {
    const tableId = this.value;
    // Save selection in localStorage
    localStorage.setItem('selectedReturnsTable', tableId);
    
    if (tableId === 'upload') {
      // Trigger file input when upload option is selected
      document.getElementById('fileInput').click();
      this.selectedIndex = 0;
    } else if (tableId.startsWith('delete_')) {
      const id = tableId.replace('delete_', '');
      fetch(`/drop_table/${id}`, { method: 'POST' })
        .then(r => r.json())
        .then(() => location.reload())
        .catch(e => console.error('Delete error:', e));
    } else if (tableId) {
      // Fetch and display selected table data
      fetch(`/get_table/${tableId}`)
        .then(response => response.json())
        .then(data => {
          const container = document.querySelector('.table-container') || createTableContainer();
          container.innerHTML = data.table_html;
          initDataTable();
        })
        .catch(error => console.error('Error:', error));
    }
  });
}

function updateDropdownOptions(tables) {
  const dropdown = document.getElementById('returnsTableSelect');
  // Store the current selection
  const currentSelection = dropdown.value;
  
  // Clear existing options
  dropdown.innerHTML = '';
  
  // Add default options
  dropdown.appendChild(new Option('Select Returns Table', ''));
  dropdown.appendChild(new Option('Upload New Table...', 'upload'));
  
  // Add table options
  tables.forEach(table => {
    dropdown.appendChild(new Option(table.name, table.id));
  });

  // Restore selection if it still exists
  if (tables.some(t => t.id.toString() === currentSelection)) {
    dropdown.value = currentSelection;
  }
}

function createTableContainer() {
  const container = document.createElement('div');
  container.className = 'table-container';
  document.body.appendChild(container);
  return container;
}

// Apply ACD row styles
function applyACDRowStyles() {
  $('#returnsTable tbody tr').each(function() {
    if ($(this).find("td[data-acd='1']").length > 0) {
      $(this).addClass('acd-row');
    } else {
      $(this).removeClass('acd-row');
    }
  });
}

// Function to handle file uploads
function fileUploadHandler(e) {
  console.log("fileUploadHandler triggered");
  if (this.files.length > 0) {
    const formData = new FormData();
    formData.append('file', this.files[0]);
    
    // Send file to server for processing
    fetch('/', {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        console.error('Upload error:', data.error);
        alert(data.error);
        return;
      }
      // Update table content and dropdown
      const container = document.querySelector('.table-container') || createTableContainer();
      container.innerHTML = data.table_html;
      updateDropdownOptions(data.tables);
      if (data.selected_table_id) {
        localStorage.setItem('selectedReturnsTable', data.selected_table_id);
        document.getElementById('returnsTableSelect').value = data.selected_table_id;
      }
      const debugInfo = document.getElementById('debugDropdown');
      if (debugInfo && data.debug_info_html) {
        debugInfo.innerHTML = data.debug_info_html;
      }
      // Initialize DataTable
      initDataTable();
    })
    .catch(error => {
      console.error('Error:', error);
      alert('Error uploading file: ' + error);
    });
  }
}

// Initial call to set up event listeners
attachEventListeners();