
// Wait for the document to be fully loaded before initializing
$(document).ready(function() {
  // Initialize DataTable if a table exists on page load
  if (document.querySelector('#returnsTable')) {
    initDataTable();
  }
});

/**
 * Initializes or reinitializes the DataTable with custom configuration
 * Destroys existing instance if it exists to prevent duplicates
 */
function initDataTable() {
  // Clean up existing DataTable instance if present
  if ($.fn.DataTable.isDataTable('#returnsTable')) {
    $('#returnsTable').DataTable().destroy();
  }
  // Configure and initialize new DataTable
  $('#returnsTable').DataTable({
    paging: true,          // Enable pagination
    pageLength: 10,        // Show 10 rows per page
    searching: true,       // Enable search functionality
    ordering: true,        // Enable column sorting
    scrollX: true,         // Enable horizontal scrolling
    dom: 'Bfrtip',        // Layout with buttons
    buttons: ['copy','csv','excel','print'], // Export options
    // Attach popup listeners after table initialization
    initComplete: function(settings, json) {
      if (window.attachPopupListeners) {
        window.attachPopupListeners();
      }
    },
    // Attach popup listeners after table redraws
    drawCallback: function(settings) {
      if (window.attachPopupListeners) {
        window.attachPopupListeners();
      }
    }
  });
}

/**
 * Sets up event listeners for ReturnsTable selection and file uploads
 */
function attachEventListeners() {
  document.getElementById('returnsTableSelect').addEventListener('change', function() {
    const tableId = this.value;
    if (tableId === 'upload') {
      // Trigger file input when upload option is selected
      document.getElementById('fileInput').click();
      this.selectedIndex = 0;
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

  // Handle file upload events
  document.getElementById('fileInput').addEventListener('change', function(e) {
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

        // Update table content
        const container = document.querySelector('.table-container') || createTableContainer();
        container.innerHTML = data.table_html;

        // Update dropdown menu without replacing the entire document
        updateDropdownOptions(data.tables);

        // Update debug info
        const debugInfo = document.querySelector('.debug-info');
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
  });

  // Remove the attachPopupListeners call at the end since it's handled by popup.js
}

// Add new helper function to update dropdown options
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

// Replace the script that created a table-container if absent
function createTableContainer() {
  const container = document.createElement('div');
  container.className = 'table-container';
  document.body.appendChild(container);
  return container;
}

// Initial call to set up everything
attachEventListeners();