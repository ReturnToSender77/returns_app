$(document).ready(function() {
  // If a table is initially rendered, call initDataTable once
  if (document.querySelector('#returnsTable')) {
    initDataTable();
  }
});

function initDataTable() {
  if ($.fn.DataTable.isDataTable('#returnsTable')) {
    $('#returnsTable').DataTable().destroy();
  }
  $('#returnsTable').DataTable({
    paging: true,
    pageLength: 10,
    searching: true,
    ordering: true,
    scrollX: true,
    dom: 'Bfrtip',
    buttons: ['copy','csv','excel','print'],
    initComplete: function(settings, json) {
      if (window.attachPopupListeners) {
        window.attachPopupListeners();
      }
    },
    drawCallback: function(settings) {
      if (window.attachPopupListeners) {
        window.attachPopupListeners();
      }
    }
  });
}

function attachEventListeners() {
  document.getElementById('returnsTableSelect').addEventListener('change', function() {
    const tableId = this.value;
    if (tableId === 'upload') {
      document.getElementById('fileInput').click();
      this.selectedIndex = 0;
    } else if (tableId) {
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

  document.getElementById('fileInput').addEventListener('change', function(e) {
    if (this.files.length > 0) {
      const formData = new FormData();
      formData.append('file', this.files[0]);
      
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