// Initialize selected fields array and other variables
let selectedFactivaFields = [];
let currentTableId = null;
let hasArticles = false; // Global flag to track if articles are available

// Make sure DOM is loaded before attaching event listeners
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM loaded - initializing Factiva integration');
  
  // Get references to important elements
  const tableSelector = document.getElementById('returnsTableSelectChron');
  const mergeButton = document.getElementById('mergeFactivaData');
  
  if (!tableSelector) {
    console.error("Could not find table selector element!");
    return;
  }
  
  if (!mergeButton) {
    console.error("Could not find merge button element!");
    return;
  }
  
  // Initialize checkbox listeners
  initializeFactivaFieldCheckboxes();
  
  // Table selection change handler
  tableSelector.addEventListener('change', function() {
    const tableId = this.value;
    console.log('Table selection changed to:', tableId);
    
    // Set global currentTableId
    currentTableId = tableId;
    
    // Also update hidden field if it exists
    const hiddenField = document.getElementById('returnsTableId');
    if (hiddenField) hiddenField.value = tableId || "";
    
    // If no table selected, clear UI and disable merge button
    if (!tableId) {
      document.getElementById('factivaArticlesList').innerHTML = '<li>No Factiva articles available</li>';
      hasArticles = false;
      updateMergeButtonState();
      return;
    }
    
    // Fetch factiva articles for this table - use the new metadata endpoint
    fetchFactivaMetadata(tableId);
  });
  
  // Use the window.factivaMerge.perform method for actual processing
  mergeButton.onclick = function(event) {
    console.log('Merge button clicked directly!');
    event.preventDefault();
    
    // Use the factivaMerge object's method if available, otherwise fall back to our local function
    if (window.factivaMerge && typeof window.factivaMerge.perform === 'function') {
      window.factivaMerge.perform();
    } else {
      processMergeRequest();
    }
  };
  
  // Set initial table ID if a table is already selected on page load
  if (tableSelector.value) {
    currentTableId = tableSelector.value;
    console.log('Initial table ID from selector:', currentTableId);
    fetchFactivaMetadata(currentTableId);
  }
  
  // Force first update of merge button state
  setTimeout(updateMergeButtonState, 500);
});

// Process the merge request
function processMergeRequest() {
  console.log('Processing merge request with:', {
    tableId: currentTableId,
    hasArticles: hasArticles,
    selectedFields: selectedFactivaFields
  });
  
  // Validate we have what we need
  if (!currentTableId) {
    alert('Please select a returns table first');
    console.error('No table ID available');
    return;
  }
  
  if (selectedFactivaFields.length === 0) {
    alert('Please select at least one field to merge');
    console.error('No fields selected');
    return;
  }
  
  // Show merge in progress
  const statusDiv = document.getElementById('mergeStatus');
  if (statusDiv) {
    statusDiv.textContent = 'Adding Factiva column... This may take a moment.';
    statusDiv.className = 'alert alert-info mt-2';
    statusDiv.style.display = 'block';
  }
  
  // Use the new /add_factiva_column endpoint with the selected fields
  fetch('/add_factiva_column', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      table_id: currentTableId,
      selected_fields: selectedFactivaFields
    })
  })
  .then(response => {
    console.log('Server response status:', response.status);
    return response.json();
  })
  .then(data => {
    console.log('Server response data:', data);
    
    // Show result message
    if (statusDiv) {
      if (data.error) {
        statusDiv.textContent = `Error: ${data.error}`;
        statusDiv.className = 'alert alert-danger mt-2';
      } else {
        statusDiv.textContent = data.message || "Factiva column added successfully";
        statusDiv.className = 'alert alert-success mt-2';
        
        // Refresh the returns table to show the new column
        refreshReturnsTable();
        
        // Uncheck all fields
        document.querySelectorAll('.factiva-field:checked').forEach(cb => {
          cb.checked = false;
        });
        selectedFactivaFields = [];
        updateMergeButtonState();
      }
    }
  })
  .catch(error => {
    console.error('Error adding factiva column:', error);
    if (statusDiv) {
      statusDiv.textContent = 'Error adding Factiva column. See console for details.';
      statusDiv.className = 'alert alert-danger mt-2';
    }
  });
}

// Fetch factiva metadata for a specific table
function fetchFactivaMetadata(tableId) {
  if (!tableId) return;
  
  fetch(`/get_factiva_metadata/${tableId}`)
    .then(res => res.json())
    .then(data => {
      const ul = document.getElementById('factivaArticlesList');
      
      if (data.error) {
        ul.innerHTML = `<li>Error: ${data.error}</li>`;
        hasArticles = false;
        updateMergeButtonState();
        return;
      }
      
      // Group articles by date
      const articlesByDate = {};
      const articles = data.articles || [];
      
      articles.forEach(article => {
        if (!article.publish_date) return;
        
        // Extract just the date part
        const datePart = article.publish_date.split('T')[0];
        
        if (!articlesByDate[datePart]) {
          articlesByDate[datePart] = [];
        }
        
        articlesByDate[datePart].push(article);
      });
      
      // Update the articles list with grouped counts
      if (Object.keys(articlesByDate).length > 0) {
        let content = '';
        
        // Sort dates chronologically
        const sortedDates = Object.keys(articlesByDate).sort();
        
        sortedDates.forEach(date => {
          const articles = articlesByDate[date];
          const formattedDate = new Date(date).toLocaleDateString();
          
          content += `<li data-article-available="true">
                      <strong>${formattedDate}</strong>: 
                      ${articles.length} article${articles.length !== 1 ? 's' : ''}
                      </li>`;
        });
        
        ul.innerHTML = content;
        hasArticles = true;
        console.log(`Loaded ${articles.length} factiva articles across ${sortedDates.length} dates`);
      } else {
        ul.innerHTML = '<li>No factiva articles available</li>';
        hasArticles = false;
      }
      
      // Always update button state after loading articles
      updateMergeButtonState();
    })
    .catch(err => {
      console.error("Error fetching factiva metadata:", err);
      document.getElementById('factivaArticlesList').innerHTML = '<li>Error fetching articles</li>';
      hasArticles = false;
      updateMergeButtonState();
    });
}

// Initialize Factiva field checkboxes
function initializeFactivaFieldCheckboxes() {
  console.log('Initializing Factiva field checkboxes');
  const checkboxes = document.querySelectorAll('.factiva-field');
  console.log(`Found ${checkboxes.length} factiva field checkboxes`);
  
  checkboxes.forEach(checkbox => {
    // Remove existing listeners before adding new one to avoid duplicates
    checkbox.removeEventListener('change', checkboxChangeHandler);
    checkbox.addEventListener('change', checkboxChangeHandler);
  });
}

// Handle checkbox changes
function checkboxChangeHandler() {
  console.log(`Checkbox ${this.id} changed to ${this.checked}`);
  
  // Update selected fields array
  selectedFactivaFields = Array.from(
    document.querySelectorAll('.factiva-field:checked')
  ).map(cb => cb.value);
  
  console.log('Selected fields:', selectedFactivaFields);
  
  // Update merge button state
  updateMergeButtonState();
  
  // Also update the factivaMerge object's selected fields
  if (window.factivaMerge && typeof window.factivaMerge.updateSelectedFields === 'function') {
    window.factivaMerge.updateSelectedFields();
  }
}

// Helper function to update the merge button state
function updateMergeButtonState() {
  const mergeButton = document.getElementById('mergeFactivaData');
  if (!mergeButton) {
    console.log('Merge button not found in DOM');
    return;
  }
  
  // Get selected fields
  const fieldCheckboxes = document.querySelectorAll('.factiva-field:checked');
  const fieldsSelected = fieldCheckboxes.length > 0;
  
  // Check if there are any true articles by looking at the list items
  const articleItems = document.querySelectorAll('#factivaArticlesList li');
  let hasRealArticles = false;
  
  articleItems.forEach(item => {
    if (item.dataset.articleAvailable === "true" || 
        (!item.textContent.toLowerCase().includes('no factiva') && 
         !item.textContent.toLowerCase().includes('no article'))) {
      hasRealArticles = true;
    }
  });
  
  hasArticles = hasArticles || hasRealArticles;
  
  // Simple conditions for enabling the button:
  // 1. We have a selected table
  // 2. We have articles available or set the hasArticles flag from before
  // 3. At least one field is selected
  const shouldEnable = currentTableId && (hasArticles || hasRealArticles) && fieldsSelected;
  
  // Set button state
  mergeButton.disabled = !shouldEnable;
  
  // Log current state for debugging
  console.log('Button state updated:', {
    currentTableId: currentTableId,
    hasArticles: hasArticles,
    hasRealArticles: hasRealArticles,
    fieldsSelected: fieldsSelected,
    shouldEnable: shouldEnable,
    isDisabled: mergeButton.disabled
  });
  
  // Visual feedback
  if (mergeButton.disabled) {
    mergeButton.classList.add('btn-disabled');
    mergeButton.title = "Select a returns table, ensure articles are available, and select fields";
  } else {
    mergeButton.classList.remove('btn-disabled');
    mergeButton.title = "Click to merge selected fields";
  }

  // Update debug info if available
  const debugInfoEl = document.getElementById('mergeDebugInfo');
  if (debugInfoEl) {
    debugInfoEl.textContent = 
      `Table ID: ${currentTableId}\n` +
      `Has Articles: ${hasArticles}\n` +
      `Selected Fields: ${selectedFactivaFields.join(', ')}\n` +
      `Button Enabled: ${!mergeButton.disabled}`;
  }
}

// Helper function to refresh the returns table display
function refreshReturnsTable() {
  if (!currentTableId) return;
  
  // Use the global loadReturnTable function if available
  if (typeof window.loadReturnTable === 'function') {
    window.loadReturnTable(currentTableId);
    return;
  }
  
  // Otherwise use our original implementation
  fetch(`/get_table/${currentTableId}`)
    .then(response => response.json())
    .then(data => {
      if(data.error) {
        console.error(data.error);
        return;
      }
      
      // Parse the HTML to extract the table data
      const parser = new DOMParser();
      const doc = parser.parseFromString(data.table_html, 'text/html');
      const table = doc.querySelector('#returnsTable');
      
      if(!table) {
        document.getElementById('chronTableHead').innerHTML = '<tr><th colspan="100%">No data available in table</th></tr>';
        document.getElementById('chronTableBody').innerHTML = '<tr><td colspan="100%" class="text-center">Table not found</td></tr>';
        return;
      }
      
      // Extract column headers
      const headerRow = table.querySelector('thead tr');
      const headers = Array.from(headerRow.querySelectorAll('th')).map(th => th.textContent);
      
      // Create header row for our chronology table
      let headerHtml = '<tr>';
      headers.forEach(header => {
        headerHtml += `<th>${header}</th>`;
      });
      headerHtml += '</tr>';
      document.getElementById('chronTableHead').innerHTML = headerHtml;
      
      // Extract data rows
      const rows = Array.from(table.querySelectorAll('tbody tr'));
      let rowsHtml = '';
      
      if (rows.length === 0) {
        rowsHtml = '<tr><td colspan="' + headers.length + '" class="text-center">No data available</td></tr>';
      } else {
        rows.forEach(row => {
          const cells = Array.from(row.querySelectorAll('td'));
          if(cells.length > 0) {
            rowsHtml += '<tr>';
            cells.forEach(cell => {
              // Check for special cell types
              const isAcd = cell.getAttribute('data-acd') === '1';
              const isFactivaCell = cell.classList.contains('factiva-cell');
              
              let cellClass = '';
              if (isAcd) cellClass = 'acd-cell';
              if (isFactivaCell) cellClass = 'factiva-cell';
              
              rowsHtml += `<td class="${cellClass}">${cell.textContent}</td>`;
            });
            rowsHtml += '</tr>';
          }
        });
      }
      
      document.getElementById('chronTableBody').innerHTML = rowsHtml;
      
      // Show table headers
      document.getElementById('tableHeaders').innerHTML = '<h3 class="mt-3">Table Columns: ' + headers.join(', ') + '</h3>';
      
      // Reinitialize footnote system after table refresh
      setTimeout(() => {
        if (typeof window.initFootnoteSystem === 'function') {
          window.initFootnoteSystem();
        }
      }, 300);
    })
    .catch(error => {
      console.error('Error refreshing table data:', error);
    });
}

// Make functions globally available
window.updateMergeButtonState = updateMergeButtonState;
window.refreshReturnsTable = refreshReturnsTable;
window.fetchFactivaMetadata = fetchFactivaMetadata;
