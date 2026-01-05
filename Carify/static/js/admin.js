document.addEventListener('DOMContentLoaded', function () {
  // Add simple alerts for demo buttons
  const approveBtns = document.querySelectorAll('a.text-success');
  approveBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      alert('Redirecting to Next Page');
    });
  });

  // Confirm deletion globally
  const deleteLinks = document.querySelectorAll('a.text-danger');
  deleteLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      const confirmed = confirm("Are you sure you want to delete this?");
      if (!confirmed) e.preventDefault();
    });
  });

  // Table enhancements (basic zebra striping using JS, if not CSS handled)
  const tables = document.querySelectorAll('table');
  tables.forEach(table => {
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach((row, index) => {
      if (index % 2 === 0) {
        row.style.backgroundColor = '#f39a9a';
        

      }
    });
  });
});
