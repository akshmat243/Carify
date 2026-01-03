document.addEventListener('DOMContentLoaded', function () {
  // Add Row on "Create" Button Click
  document.getElementById('Floor-Carpets').addEventListener('click', function () {
    const tableBody = document.getElementById('interior-body');
    const firstRow = tableBody.rows[0];
    const newRow = firstRow.cloneNode(true);

    // Reset input values and select dropdowns
    newRow.querySelectorAll('input, select').forEach((el) => {
      if (el.tagName === 'SELECT') {
        el.selectedIndex = 0;
      } else {
        el.value = '';
      }

      // Hide custom inputs again
      if (el.classList.contains('customInput')) {
        el.style.display = 'none';
      }
    });

    tableBody.appendChild(newRow);
  });

  // Show/Hide Custom Input if "Other..." selected
  document.addEventListener('change', function (e) {
    if (e.target.tagName === 'SELECT') {
      const nextInput = e.target.nextElementSibling;

      if (
        nextInput &&
        nextInput.tagName === 'INPUT' &&
        nextInput.classList.contains('customInput')
      ) {
        if (e.target.value === '__custom__') {
          nextInput.style.display = 'inline-block';
        } else {
          nextInput.style.display = 'none';
          nextInput.value = ''; // Clear input if not custom
        }
      }
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  function bindDropdown(select, input) {
    if (!select || !input) return;

    select.addEventListener('change', function () {
      input.style.display = this.value === '__custom__' ? 'inline-block' : 'none';
      if (this.value !== '__custom__') input.value = '';
    });

    if (select.value === '__custom__') input.style.display = 'inline-block';
  }

  // Bind all existing rows on load
  document.querySelectorAll('tr').forEach(row => {
    bindDropdown(row.querySelector('.categoryDropdown'), row.querySelector('.customCategoryInput'));
    bindDropdown(row.querySelector('.areaDropdown'), row.querySelector('.customAreaInput'));
  });
});
