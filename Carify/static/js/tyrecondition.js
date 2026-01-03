document.addEventListener('DOMContentLoaded', function () {
  const statuses = JSON.parse(document.getElementById('statuses-data').textContent);

  function bindDropdown(select, input) {
    if (!select || !input) return;
    select.addEventListener('change', function () {
      input.style.display = this.value === '__custom__' ? 'block' : 'none';
      if (this.value !== '__custom__') input.value = '';
    });
    if (select.value === '__custom__') input.style.display = 'block';
  }

  document.querySelectorAll('tr').forEach(row => {
    bindDropdown(row.querySelector('select.statusDropdown'), row.querySelector('input.customConditionInput'));
  });
});
