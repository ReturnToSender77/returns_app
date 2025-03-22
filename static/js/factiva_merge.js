// Simple and direct factiva merge functionality

// Keep track of selected fields and table
let factivaMergeState = {
  tableId: null,
  selectedFields: []
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  console.log('Factiva merge module loaded');
  
  // Get the current table ID
  const tableSelect = document.getElementById('returnsTableSelectChron');
  if (tableSelect && tableSelect.value) {
    factivaMergeState.tableId = tableSelect.value;
    console.log('Initial table ID:', factivaMergeState.tableId);
    
    // Load articles for the initial table
    loadFactivaArticles(factivaMergeState.tableId);
  }
  
  // Listen for table selection changes
  if (tableSelect) {
    tableSelect.addEventListener('change', function() {
      factivaMergeState.tableId = this.value;
      console.log('Table ID updated:', factivaMergeState.tableId);
      
      // The table change handler in chron_tables.js will call loadFactivaArticles
      updateMergeButtonState();
    });
  }
  
  // Hook up checkbox listeners
  document.querySelectorAll('.factiva-field').forEach(checkbox => {
    checkbox.addEventListener('change', function() {
      updateSelectedFields();
    });
  });
  
  // Update button state initially
  setTimeout(updateMergeButtonState, 200);
});

// Load Factiva articles for a specific table
function loadFactivaArticles(tableId) {
  if (!tableId) {
    console.log('No table ID provided to load articles');
    return;
  }

  console.log('Loading Factiva articles for table:', tableId);
  
  fetch(`/get_factiva_articles/${tableId}`)
    .then(res => res.json())
    .then(data => {
      const ul = document.getElementById('factivaArticlesList');
      if (!ul) {
        console.error('Could not find factivaArticlesList element');
        return;
      }
      
      if (data.error) {
        ul.innerHTML = `<li>Error: ${data.error}</li>`;
        return;
      }
      
      if (data.factiva_articles && data.factiva_articles.length > 0) {
        console.log(`Found ${data.factiva_articles.length} Factiva articles`);
        let content = '';
        data.factiva_articles.forEach(article => {
          content += `<li data-article-available="true"><strong>${article.headline}</strong> by ${article.author}</li>`;
        });
        ul.innerHTML = content;
      } else {
        ul.innerHTML = '<li>No Factiva articles available</li>';
      }
      
      // Update merge button state
      updateMergeButtonState();
    })
    .catch(err => {
      console.error("Error fetching factiva articles:", err);
      const ul = document.getElementById('factivaArticlesList');
      if (ul) {
        ul.innerHTML = '<li>Error fetching articles</li>';
      }
    });
}

// Update the list of selected fields
function updateSelectedFields() {
  factivaMergeState.selectedFields = Array.from(
    document.querySelectorAll('.factiva-field:checked')
  ).map(cb => cb.value);
  
  console.log('Selected fields updated:', factivaMergeState.selectedFields);
  updateMergeButtonState();
  
  // Update debug info if available
  const debugInfoEl = document.getElementById('mergeDebugInfo');
  if (debugInfoEl) {
    const hasArticles = checkIfArticlesAvailable();
    debugInfoEl.textContent = 
      `Table ID: ${factivaMergeState.tableId}\n` +
      `Has Articles: ${hasArticles}\n` +
      `Selected Fields: ${factivaMergeState.selectedFields.join(', ')}\n` +
      `Button Enabled: ${!document.getElementById('mergeFactivaData').disabled}`;
  }
}

// Check if factiva articles are available
function checkIfArticlesAvailable() {
  const articleItems = document.querySelectorAll('#factivaArticlesList li');
  if (articleItems.length === 0) return false;
  
  // If there's one item and it says "no articles", return false
  if (articleItems.length === 1) {
    const firstText = articleItems[0].textContent.toLowerCase();
    if (firstText.includes('no factiva') || firstText.includes('no article')) {
      return false;
    }
  }
  
  // Otherwise assume we have articles
  return true;
}

// Update merge button state
function updateMergeButtonState() {
  const mergeButton = document.getElementById('mergeFactivaData');
  if (!mergeButton) return;
  
  const hasArticles = checkIfArticlesAvailable();
  const hasSelectedFields = factivaMergeState.selectedFields.length > 0;
  const hasTable = !!factivaMergeState.tableId;
  
  const shouldEnable = hasTable && hasArticles && hasSelectedFields;
  
  console.log('Merge button state check:', { 
    hasTable, hasArticles, hasSelectedFields, shouldEnable 
  });
  
  mergeButton.disabled = !shouldEnable;
  
  if (!shouldEnable) {
    mergeButton.classList.add('btn-disabled');
  } else {
    mergeButton.classList.remove('btn-disabled');
  }
}

// The main merge function - called directly from HTML
function performMerge() {
  console.log('MERGE BUTTON CLICKED');
  
  // Basic validation
  if (!factivaMergeState.tableId) {
    alert('Please select a returns table first');
    return;
  }
  
  if (factivaMergeState.selectedFields.length === 0) {
    alert('Please select at least one field to merge');
    return;
  }
  
  // Show merge in progress
  const statusDiv = document.getElementById('mergeStatus');
  if (statusDiv) {
    statusDiv.textContent = 'Merging data... This may take a moment.';
    statusDiv.className = 'alert alert-info mt-2';
    statusDiv.style.display = 'block';
  }
  
  console.log('Sending merge request with:', {
    table_id: factivaMergeState.tableId,
    selected_columns: factivaMergeState.selectedFields
  });
  
  // Send the request
  fetch('/merge_factiva_data', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      table_id: factivaMergeState.tableId,
      selected_columns: factivaMergeState.selectedFields
    })
  })
  .then(response => response.json())
  .then(data => {
    console.log('Server response:', data);
    
    if (data.error) {
      if (statusDiv) {
        statusDiv.textContent = `Error: ${data.error}`;
        statusDiv.className = 'alert alert-danger mt-2';
      } else {
        alert(`Error: ${data.error}`);
      }
      return;
    }
    
    // Success! Show message
    if (statusDiv) {
      statusDiv.textContent = data.message;
      statusDiv.className = 'alert alert-success mt-2';
    } else {
      alert(`Success: ${data.message}`);
    }
    
    // Uncheck all fields
    document.querySelectorAll('.factiva-field:checked').forEach(cb => {
      cb.checked = false;
    });
    updateSelectedFields();
    
    // Refresh the table display
    refreshChronTable();
    
    // Hide the status message after a delay
    if (statusDiv) {
      setTimeout(() => {
        statusDiv.style.display = 'none';
      }, 5000);
    }
  })
  .catch(error => {
    console.error('Error during merge operation:', error);
    
    if (statusDiv) {
      statusDiv.textContent = 'Error merging data. See console for details.';
      statusDiv.className = 'alert alert-danger mt-2';
    } else {
      alert('Error merging data. See console for details.');
    }
  });
}

// Refresh the table after a merge
function refreshChronTable() {
  console.log('Refreshing chronology table');
  
  // The simplest way is to trigger the change event on the table selector
  const tableSelect = document.getElementById('returnsTableSelectChron');
  if (tableSelect) {
    const event = new Event('change');
    tableSelect.dispatchEvent(event);
  }
}

// Expose the public API
window.factivaMerge = {
  perform: performMerge,
  updateSelectedFields: updateSelectedFields
};
window.loadFactivaArticles = loadFactivaArticles;
