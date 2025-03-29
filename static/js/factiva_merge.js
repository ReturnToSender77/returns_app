/**
 * Factiva Article Integration
 * Handles merging Factiva article data with returns tables
 */

// FactivaMerge singleton object
const factivaMerge = (function() {
  // Private variables
  let selectedFields = [];
  let currentTableId = null;
  let articlesByDate = {};
  let hasLoadedArticles = false;

  // Initialize when returns table is selected
  function init(tableId) {
    if (!tableId) return;
    
    currentTableId = tableId;
    console.log(`Initializing Factiva merge for table ID ${tableId}`);
    
    // Reset state
    selectedFields = [];
    articlesByDate = {};
    hasLoadedArticles = false;
    
    // Check if we should enable the merge button
    updateMergeButtonState();
    
    // Load articles for the selected table
    loadArticlesForTable(tableId);
  }
  
  // Load Factiva articles for a table and organize them by date
  function loadArticlesForTable(tableId) {
    console.log(`Loading Factiva articles for table ${tableId}`);
    
    // Show loading status
    updateMergeStatus("Loading articles...", "info");
    
    fetch(`/get_factiva_metadata/${tableId}`)
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          console.error(`Error loading articles: ${data.error}`);
          updateMergeStatus(`Error: ${data.error}`, "danger");
          return;
        }
        
        const articles = data.articles || [];
        console.log(`Loaded ${articles.length} Factiva articles`);
        
        // Group articles by date
        articlesByDate = {};
        articles.forEach(article => {
          if (!article.publish_date) return;
          
          // Extract just the date part (ignore time)
          const datePart = article.publish_date.split('T')[0];
          
          if (!articlesByDate[datePart]) {
            articlesByDate[datePart] = [];
          }
          
          articlesByDate[datePart].push(article);
        });
        
        // Update status
        if (articles.length > 0) {
          const dateCount = Object.keys(articlesByDate).length;
          updateMergeStatus(`Found ${articles.length} articles across ${dateCount} dates`, "success");
          hasLoadedArticles = true;
        } else {
          updateMergeStatus("No Factiva articles found for this table", "warning");
          hasLoadedArticles = false;
        }
        
        // Update debug info
        updateDebugInfo();
        
        // Update UI
        displayArticleSummary(articlesByDate);
        updateMergeButtonState();
      })
      .catch(error => {
        console.error("Error fetching articles:", error);
        updateMergeStatus(`Error: ${error.message}`, "danger");
      });
  }
  
  // Update the merge button state based on selections and article availability
  function updateMergeButtonState() {
    const mergeButton = document.getElementById('mergeFactivaData');
    if (!mergeButton) return;
    
    const hasSelectedFields = selectedFields.length > 0;
    const hasTable = currentTableId !== null;
    
    // Only enable the button if we have articles, a table is selected, and fields are selected
    const shouldEnable = hasLoadedArticles && hasTable && hasSelectedFields;
    
    mergeButton.disabled = !shouldEnable;
    if (shouldEnable) {
      mergeButton.classList.remove('btn-disabled');
    } else {
      mergeButton.classList.add('btn-disabled');
    }
    
    // Update debug info
    updateDebugInfo();
  }
  
  // Update selected fields based on checkboxes
  function updateSelectedFields() {
    selectedFields = [];
    document.querySelectorAll('.factiva-field:checked').forEach(checkbox => {
      selectedFields.push(checkbox.value);
    });
    
    console.log('Selected fields updated:', selectedFields);
    updateMergeButtonState();
    updateDebugInfo();
  }
  
  // Display a summary of available articles
  function displayArticleSummary(articlesByDate) {
    const articlesList = document.getElementById('factivaArticlesList');
    if (!articlesList) return;
    
    if (Object.keys(articlesByDate).length === 0) {
      articlesList.innerHTML = '<li>No articles available</li>';
      return;
    }
    
    let html = '';
    // Sort dates chronologically
    const sortedDates = Object.keys(articlesByDate).sort();
    
    for (const date of sortedDates) {
      const articles = articlesByDate[date];
      const formattedDate = new Date(date).toLocaleDateString();
      
      html += `<li><strong>${formattedDate}</strong>: ${articles.length} article${articles.length !== 1 ? 's' : ''}</li>`;
    }
    
    articlesList.innerHTML = html;
  }
  
  // Update merge status message
  function updateMergeStatus(message, type) {
    const statusEl = document.getElementById('mergeStatus');
    if (!statusEl) return;
    
    statusEl.textContent = message;
    statusEl.className = `alert alert-${type}`;
    statusEl.style.display = message ? 'block' : 'none';
  }
  
  // Update debug info
  function updateDebugInfo() {
    const debugEl = document.getElementById('mergeDebugInfo');
    if (!debugEl) return;
    
    const debug = {
      currentTableId,
      selectedFields,
      articleDates: Object.keys(articlesByDate),
      articleCount: Object.values(articlesByDate).reduce((sum, arr) => sum + arr.length, 0),
      hasLoadedArticles,
      mergeButtonEnabled: !document.getElementById('mergeFactivaData')?.disabled
    };
    
    debugEl.textContent = JSON.stringify(debug, null, 2);
  }
  
  // Perform the merge operation
  function performMerge() {
    if (!currentTableId || selectedFields.length === 0 || !hasLoadedArticles) {
      updateMergeStatus("Cannot merge: missing required data", "danger");
      return;
    }
    
    console.log(`Performing merge for table ${currentTableId} with fields:`, selectedFields);
    updateMergeStatus("Merging Factiva data...", "info");
    
    // Call the server to perform the merge
    fetch('/add_factiva_column', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        table_id: currentTableId,
        selected_fields: selectedFields
      }),
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      if (data.error) {
        updateMergeStatus(`Error: ${data.error}`, "danger");
        return;
      }
      
      console.log('Merge successful:', data);
      updateMergeStatus(`Success! ${data.message}`, "success");
      
      // Reload the returns table to show the new columns
      if (window.loadReturnTable) {
        window.loadReturnTable(currentTableId);
      }
    })
    .catch(error => {
      console.error('Merge error:', error);
      updateMergeStatus(`Error: ${error.message}`, "danger");
    });
  }
  
  // Public API
  return {
    init,
    updateSelectedFields,
    perform: performMerge
  };
})();

// Set up global access
window.factivaMerge = factivaMerge;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  // Set up table selection listener
  const tableSelect = document.getElementById('returnsTableSelectChron');
  if (tableSelect) {
    tableSelect.addEventListener('change', function() {
      if (this.value) {
        factivaMerge.init(this.value);
      }
    });
    
    // Initialize with current value if present
    if (tableSelect.value) {
      factivaMerge.init(tableSelect.value);
    }
  }
});
