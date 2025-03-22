/**
 * Chron Tables - Manages dual table functionality for the chronology page
 */

// Global variables to store column data
let returnTableColumns = []; // Array of column objects with name and data
let chronTableColumns = [];  // Array of selected column objects
let draggedColumnIndex = null;

// Initialize the two tables
document.addEventListener('DOMContentLoaded', function() {
  console.log('Chron tables module loaded');

  // Listen for returns table selection change
  document.getElementById('returnsTableSelectChron').addEventListener('change', function() {
    loadReturnTable(this.value);
    clearChronTable(); // Always clear the chron table when a new returns table is selected
  });

  // Listen for export button clicks - Override the default handlers
  document.getElementById('exportToExcel').addEventListener('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    exportChronTableToExcel();
    return false;
  });

  document.getElementById('exportToStyledExcel').addEventListener('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    exportChronTableToStyledExcel();
    return false;
  });

  // Initialize dragover event handler for the chronTable
  const customChronTable = document.getElementById('customChronTable');
  if (customChronTable) {
    customChronTable.addEventListener('dragover', function(e) {
      e.preventDefault(); // Allow drop
    });
  }

  // Initialize the tables if a return table is already selected
  const selectedTable = document.getElementById('returnsTableSelectChron').value;
  if (selectedTable) {
    loadReturnTable(selectedTable);
    // Make sure the chron table starts empty
    clearChronTable();
  }
});

// Load data into the returns table only
function loadReturnTable(tableId) {
  if (!tableId) {
    clearReturnTable();
    return;
  }

  fetch(`/get_table/${tableId}`)
    .then(response => response.json())
    .then(data => {
      if(data.error) {
        console.error(data.error);
        clearReturnTable();
        return;
      }
      
      // Parse the HTML to extract the table data
      const parser = new DOMParser();
      const doc = parser.parseFromString(data.table_html, 'text/html');
      const table = doc.querySelector('#returnsTable');
      
      if(!table) {
        clearReturnTable();
        return;
      }
      
      // Extract column headers and data
      const headerRow = table.querySelector('thead tr');
      const headers = Array.from(headerRow.querySelectorAll('th')).map(th => th.textContent);
      
      // Create header row for our returns table
      let headerHtml = '<tr>';
      headers.forEach((header, idx) => {
        headerHtml += `<th class="column-header" data-column-index="${idx}">${header}</th>`;
      });
      headerHtml += '</tr>';
      document.getElementById('chronTableHead').innerHTML = headerHtml;
      
      // Extract data rows
      const rows = Array.from(table.querySelectorAll('tbody tr'));
      let rowsHtml = '';
      
      if (rows.length === 0) {
        rowsHtml = '<tr><td colspan="' + headers.length + '" class="text-center">No data available</td></tr>';
      } else {
        // Extract the data into our column arrays
        returnTableColumns = headers.map((header, idx) => {
          return {
            name: header,
            index: idx,
            data: []
          };
        });

        rows.forEach(row => {
          const cells = Array.from(row.querySelectorAll('td'));
          rowsHtml += '<tr>';
          
          cells.forEach((cell, idx) => {
            // Store the data in our column objects
            if (idx < returnTableColumns.length) {
              returnTableColumns[idx].data.push(cell.textContent);
            }
            
            // Check for ACD attribute in date cells
            const isAcd = cell.getAttribute('data-acd') === '1';
            const cellClass = isAcd ? 'acd-cell' : '';
            rowsHtml += `<td class="${cellClass}">${cell.textContent}</td>`;
          });
          
          rowsHtml += '</tr>';
        });
      }
      
      document.getElementById('chronTableBody').innerHTML = rowsHtml;
      
      // Update export button states only
      const hasData = rows.length > 0;
      const hasChronColumns = chronTableColumns.length > 0;
      document.getElementById('exportToExcel').disabled = !hasData || !hasChronColumns;
      document.getElementById('exportToStyledExcel').disabled = !hasData || !hasChronColumns;
      
      console.log('Loaded returns table columns:', returnTableColumns.length);
      
      // Also make sure factiva articles are loaded
      if (window.loadFactivaArticles) {
        window.loadFactivaArticles(tableId);
      }
      
      // Initialize footnote system (which now also handles column adding)
      setTimeout(initFootnoteSystem, 300);
    })
    .catch(error => {
      console.error('Error fetching table data:', error);
      clearReturnTable();
    });
}

// Add a column from returns table to the chron table
function addColumnToChronTable(columnIndex) {
  if (columnIndex < 0 || columnIndex >= returnTableColumns.length) {
    console.error('Invalid column index:', columnIndex);
    return;
  }
  
  const columnToAdd = returnTableColumns[columnIndex];
  console.log('Adding column to chron table:', columnToAdd.name);
  
  // Check if column already exists in chron table
  if (chronTableColumns.find(col => col.name === columnToAdd.name)) {
    alert(`Column "${columnToAdd.name}" is already in the Chron Table`);
    return;
  }
  
  // Add the column to our chron table array
  chronTableColumns.push({
    name: columnToAdd.name,
    data: columnToAdd.data.slice(), // Make a copy of the data
    originalIndex: columnIndex       // Keep track of original index
  });
  
  // No need to transfer footnotes from returns table anymore as we're not storing them there
  
  // Update the chron table
  updateChronTable();
  
  // Update export buttons
  document.getElementById('exportToExcel').disabled = false;
  document.getElementById('exportToStyledExcel').disabled = false;
}

// Remove a column from the chron table
function removeColumnFromChron(columnIndex) {
  chronTableColumns.splice(columnIndex, 1);
  updateChronTable();
  
  // Disable export buttons if no columns left
  if (chronTableColumns.length === 0) {
    document.getElementById('exportToExcel').disabled = true;
    document.getElementById('exportToStyledExcel').disabled = true;
  }
}

// Update the chron table display only
function updateChronTable() {
  const chronTableHead = document.getElementById('customChronTableHead');
  const chronTableBody = document.getElementById('customChronTableBody');
  
  if (chronTableColumns.length === 0) {
    chronTableHead.innerHTML = '<tr><th colspan="100%">Add columns from the Returns Table</th></tr>';
    chronTableBody.innerHTML = '<tr><td colspan="100%" class="text-center">No columns added yet</td></tr>';
    return;
  }
  
  // Create the header row with draggable columns
  let headerHtml = '<tr>';
  chronTableColumns.forEach((col, idx) => {
    headerHtml += `
      <th class="column-header" draggable="true" data-column-index="${idx}">
        <span class="col-handle">⋮</span>${col.name}
        <span class="column-remove-btn" onclick="removeColumnFromChron(${idx})">✕</span>
      </th>`;
  });
  headerHtml += '</tr>';
  chronTableHead.innerHTML = headerHtml;
  
  // Create the data rows
  let rowsHtml = '';
  
  if (chronTableColumns.length > 0 && chronTableColumns[0].data.length > 0) {
    const rowCount = chronTableColumns[0].data.length;
    
    for (let rowIdx = 0; rowIdx < rowCount; rowIdx++) {
      rowsHtml += '<tr>';
      for (let colIdx = 0; colIdx < chronTableColumns.length; colIdx++) {
        const cellData = chronTableColumns[colIdx].data[rowIdx] || '';
        rowsHtml += `<td>${cellData}</td>`;
      }
      rowsHtml += '</tr>';
    }
  } else {
    rowsHtml = '<tr><td colspan="' + chronTableColumns.length + '" class="text-center">No data available</td></tr>';
  }
  
  chronTableBody.innerHTML = rowsHtml;
  
  // Add drag and drop functionality to column headers
  attachColumnDragEvents();
  
  // Update popups for the Chron table
  if (window.updateChronTablePopups) {
    window.updateChronTablePopups();
  }
}

// Attach drag-and-drop events to column headers
function attachColumnDragEvents() {
  const headers = document.querySelectorAll('#customChronTableHead th.column-header');
  
  headers.forEach(header => {
    // Make headers draggable
    header.setAttribute('draggable', 'true');
    
    // Drag start - store the column index being dragged
    header.addEventListener('dragstart', function(e) {
      draggedColumnIndex = parseInt(this.getAttribute('data-column-index'));
      this.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', draggedColumnIndex);
    });
    
    // Drag end - remove visual feedback
    header.addEventListener('dragend', function() {
      this.classList.remove('dragging');
      document.querySelectorAll('#customChronTableHead th').forEach(th => {
        th.classList.remove('drag-over');
      });
    });
    
    // Drag over - allow dropping and provide visual feedback
    header.addEventListener('dragover', function(e) {
      e.preventDefault();
      this.classList.add('drag-over');
    });
    
    // Drag leave - remove visual feedback
    header.addEventListener('dragleave', function() {
      this.classList.remove('drag-over');
    });
    
    // Drop - handle the column reordering
    header.addEventListener('drop', function(e) {
      e.preventDefault();
      const targetIndex = parseInt(this.getAttribute('data-column-index'));
      
      if (draggedColumnIndex !== null && draggedColumnIndex !== targetIndex) {
        reorderChronColumns(draggedColumnIndex, targetIndex);
      }
      
      this.classList.remove('drag-over');
    });
  });
}

// Reorder columns in the chronTableColumns array
function reorderChronColumns(fromIndex, toIndex) {
  if (fromIndex < 0 || fromIndex >= chronTableColumns.length || 
      toIndex < 0 || toIndex >= chronTableColumns.length) {
    return;
  }
  
  console.log(`Reordering column from index ${fromIndex} to index ${toIndex}`);
  
  // Remove the column from its current position
  const column = chronTableColumns.splice(fromIndex, 1)[0];
  
  // Insert it at the new position
  chronTableColumns.splice(toIndex, 0, column);
  
  // Update the display
  updateChronTable();
}

// Clear the returns table
function clearReturnTable() {
  document.getElementById('chronTableHead').innerHTML = '<tr><th colspan="100%">Select a returns table to load data</th></tr>';
  document.getElementById('chronTableBody').innerHTML = '<tr><td colspan="100%" class="text-center">No data available</td></tr>';
  document.getElementById('exportToExcel').disabled = true;
  document.getElementById('exportToStyledExcel').disabled = true;
  returnTableColumns = [];
}

// Clear the chron table
function clearChronTable() {
  document.getElementById('customChronTableHead').innerHTML = '<tr><th colspan="100%">Add columns from the Returns Table</th></tr>';
  document.getElementById('customChronTableBody').innerHTML = '<tr><td colspan="100%" class="text-center">No columns added yet</td></tr>';
  chronTableColumns = [];
  
  // Make sure export buttons are disabled
  document.getElementById('exportToExcel').disabled = true;
  document.getElementById('exportToStyledExcel').disabled = true;
}

// Export the chron table to Excel
function exportChronTableToExcel() {
  if (chronTableColumns.length === 0) {
    alert('Please add at least one column to the Chron Table before exporting');
    return;
  }
  
  // Get data from the chron table
  const data = [];
  
  // Extract headers
  const headers = chronTableColumns.map(col => col.name);
  data.push(headers);
  
  // Extract row data
  const rowCount = chronTableColumns[0].data.length;
  for (let i = 0; i < rowCount; i++) {
    const rowData = chronTableColumns.map(col => col.data[i]);
    data.push(rowData);
  }
  
  // Create workbook with formatting
  const ws = XLSX.utils.aoa_to_sheet(data);
  
  // Set column widths (auto-size columns)
  const colWidths = headers.map(h => ({wch: Math.max(h.length, 10)}));
  ws['!cols'] = colWidths;
  
  // Create workbook
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Chron Data");
  
  // Get the selected table name for filename
  const selectElement = document.getElementById('returnsTableSelectChron');
  const selectedText = selectElement.options[selectElement.selectedIndex].text;
  const tableName = selectedText.split('—')[0].trim() || 'Chron';
  
  // Save file
  XLSX.writeFile(wb, `${tableName}_chron_export.xlsx`);
}

// Export the chron table to styled Excel using the server endpoint
function exportChronTableToStyledExcel() {
  if (chronTableColumns.length === 0) {
    alert('Please add at least one column to the Chron Table before exporting');
    return;
  }
  
  const title = document.getElementById('excelTitle').value || 'Chron Data';
  
  // Extract data from the chron table
  const headers = chronTableColumns.map(col => col.name);
  
  // Extract row data
  const rowData = [];
  const rowCount = chronTableColumns[0].data.length;
  for (let i = 0; i < rowCount; i++) {
    const row = chronTableColumns.map(col => col.data[i]);
    rowData.push(row);
  }
  
  const tableData = [headers, ...rowData];
  
  // Get footnotes to include in the export - only chron table footnotes
  const allFootnotes = window.getFootnotes ? window.getFootnotes() : {};
  
  // Filter to only include chron table footnotes
  const footnotes = {};
  for (const [key, value] of Object.entries(allFootnotes)) {
    if (key.startsWith('chron_')) {
      footnotes[key] = value;
    }
  }
  
  // Make request to server-side API to generate the Excel file
  fetch('/export_styled_excel', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: title,
      data: tableData,
      footnotes: footnotes
    }),
  })
  .then(response => {
    if (!response.ok) throw new Error('Server response was not OK');
    return response.blob();
  })
  .then(blob => {
    // Create a URL for the blob
    const url = window.URL.createObjectURL(blob);
    
    // Create a temporary link and trigger download
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    
    // Get table name for filename
    const selectElement = document.getElementById('returnsTableSelectChron');
    const selectedText = selectElement.options[selectElement.selectedIndex].text;
    const tableName = selectedText.split('—')[0].trim() || 'Chron';
    
    a.download = `${tableName}_styled_chron_export.xlsx`;
    document.body.appendChild(a);
    a.click();
    
    // Clean up
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  })
  .catch(error => {
    console.error('Error exporting styled Excel:', error);
    alert('Failed to generate styled Excel file.');
  });
}

// Make functions globally available
window.removeColumnFromChron = removeColumnFromChron;
window.addColumnToChronTable = addColumnToChronTable; 
window.reorderChronColumns = reorderChronColumns;
