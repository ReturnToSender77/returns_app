document.getElementById('returnsTableSelectChron').addEventListener('change', function(){
  const tableId = this.value;
  document.getElementById('returnsTableId').value = tableId || "";
  
  if(!tableId) {
    document.getElementById('columnSelect').innerHTML = '<option value="" disabled selected>Select Column</option>';
    document.getElementById('factivaArticlesList').innerHTML = '<li>No Factiva articles uploaded.</li>';
    return;
  }
  
// Retrieve available columns for the selected ReturnsTable from the server and populate the dropdown
fetch(`/get_columns/${tableId}`)
    .then(res => res.json())
    .then(data => {
        if(data.error) return alert(data.error);
        const columnSelect = document.getElementById('columnSelect');
        columnSelect.innerHTML = '<option value="" disabled selected>Select Column</option>';
        data.columns.forEach(col => {
            const opt = document.createElement('option');
            opt.value = col.id;
            opt.textContent = col.name;
            columnSelect.appendChild(opt);
        });
    })
    .catch(err => console.error(err));
  
  // Fetch factiva articles corresponding to the selected ReturnsTable
  fetch(`/get_factiva_articles/${tableId}`)
    .then(res => res.json())
    .then(data => {
      const ul = document.getElementById('factivaArticlesList');
      if(data.error) {
        ul.innerHTML = `<li>Error: ${data.error}</li>`;
        return;
      }
      ul.innerHTML = '';
      if(data.factiva_articles && data.factiva_articles.length > 0) {
        data.factiva_articles.forEach(article => {
          const li = document.createElement('li');
          li.textContent = `${article.headline} by ${article.author}`;
          ul.appendChild(li);
        });
      } else {
        ul.innerHTML = '<li>No Factiva articles uploaded.</li>';
      }
    })
    .catch(err => console.error(err));
});

// Listen for changes on the ReturnsTable select element and update Factiva articles accordingly
document.getElementById('returnsTableSelectChron').addEventListener('change', function(){
    const tableId = this.value;
    const ul = document.getElementById('factivaArticlesList');
    
    // If no table is selected, display a default message and exit
    if(!tableId) {
        ul.innerHTML = '<li>No Factiva articles uploaded.</li>';
        return;
    }
    
    // Fetch Factiva articles for the selected table
    fetch(`/get_factiva_articles/${tableId}`)
        .then(res => res.json())
        .then(data => {
            if(data.error) {
                ul.innerHTML = `<li>Error: ${data.error}</li>`;
                return;
            }
            if(data.factiva_articles && data.factiva_articles.length > 0) {
                let content = '<ul>';
                data.factiva_articles.forEach(article => {
                    content += `<li>${article.headline} by ${article.author}</li>`;
                });
                content += '</ul>';
                ul.innerHTML = content;
            } else {
                ul.innerHTML = '<li>No Factiva articles uploaded.</li>';
            }
        })
        .catch(err => {
            console.error("Error fetching factiva articles:", err);
            ul.innerHTML = '<li>Error fetching articles.</li>';
        });
});

// Listen for changes on the Column select element and display the selected column 
document.getElementById('showColumn').addEventListener('click', function(){
  const columnId = document.getElementById('columnSelect').value;
  if (!columnId) return alert("Please select a column.");
  fetch(`/get_column/${columnId}`)
    .then(res => res.json())
    .then(data => {
      if(data.error) return alert(data.error);
      document.getElementById('columnDisplay').innerHTML = data.html;
    })
    .catch(err => console.error(err));
});

// Listen for Factiva upload form submission and handle the response
document.getElementById('factivaForm').addEventListener('submit', function(e){
  e.preventDefault();
  console.log("Submitting Factiva upload...");
  const formData = new FormData(this);
  fetch(this.action, { method: 'POST', body: formData })
    .then(res => {
      console.log("Response status:", res.status);
      return res.json();
    })
    .then(data => {
      console.log("Factiva upload response data:", data);
      if(data.error) {
        alert("Error: " + data.error);
        return;
      }
      alert(data.message);
      const ul = document.getElementById('factivaArticlesList');
      ul.innerHTML = '';
      if(data.factiva_articles && data.factiva_articles.length > 0) {
        data.factiva_articles.forEach(article => {
          const li = document.createElement('li');
          li.textContent = `${article.headline} by ${article.author}`;
          ul.appendChild(li);
        });
      } else {
        ul.innerHTML = '<li>No Factiva articles uploaded.</li>';
      }
    })
    .catch(err => {
      console.error("Error during Factiva upload:", err);
      alert('Error uploading factiva articles.');
    });
});
