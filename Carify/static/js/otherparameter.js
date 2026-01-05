
document.addEventListener('DOMContentLoaded', function () {
  const systems = JSON.parse(document.getElementById('performance-data').textContent);
  const statuses = JSON.parse(document.getElementById('statuses-data').textContent);

  const systemOptions = systems.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
  const statusOptions = statuses.map(s => `<option value="${s.id}">${s.name}</option>`).join('');

  function setupDynamicDropdown(select, input) {
    if (!select || !input) return;
    select.addEventListener('change', function () {
      input.style.display = this.value === '__custom__' ? 'block' : 'none';
      if (this.value !== '__custom__') input.value = '';
    });
    if (select.value === '__custom__') input.style.display = 'block';
  }

  function bindRowEvents(row) {
    setupDynamicDropdown(row.querySelector('select.systemDropdown'), row.querySelector('input.customSystemInput'));
    setupDynamicDropdown(row.querySelector('select.statusDropdown'), row.querySelector('input.customStatusInput'));
  }

  document.querySelectorAll('#other-body tr').forEach(bindRowEvents);

  const createBtn = document.getElementById('other-checks');
  createBtn.addEventListener('click', function (e) {
    e.preventDefault();

    const tbody = document.getElementById('other-body');
    const newRow = document.createElement('tr');
    newRow.innerHTML = `
      <td>
        <select name="system" class="systemDropdown">
          ${systemOptions}
          <option value="__custom__">Other...</option>
        </select>
        <input type="text" name="custom_system" class="customSystemInput" placeholder="Enter custom system" style="display: none;" />
      </td>
      <td>
        <select name="status" class="statusDropdown">
          ${statusOptions}
          <option value="__custom__">Other...</option>
        </select>
        <input type="text" name="custom_status" class="customStatusInput" placeholder="Enter custom status" style="display: none;" />
      </td>
      <td>
        <input type="text" name="recommendation" value="NIL" />
      </td>
    `;
    tbody.appendChild(newRow);
    bindRowEvents(newRow);
  });
});

