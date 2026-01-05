document.addEventListener('DOMContentLoaded', function () {
  const areas = JSON.parse(document.getElementById('glass-areas-data').textContent);
  const statuses = JSON.parse(document.getElementById('statuses-data').textContent);

  function bindDropdown(select, input) {
    if (!select || !input) return;
    select.addEventListener('change', function () {
      input.style.display = this.value === '__custom__' ? 'block' : 'none';
      if (this.value !== '__custom__') input.value = '';
    });
    if (select.value === '__custom__') input.style.display = 'block';
  }

  function bindRow(row) {
    bindDropdown(row.querySelector('select.areaDropdown'), row.querySelector('input.customAreaInput'));
    bindDropdown(row.querySelector('select.conditionDropdown'), row.querySelector('input.customConditionInput'));
  }

  document.querySelectorAll('#glass-body tr').forEach(bindRow);

  document.getElementById('Condition-of-class').addEventListener('click', function () {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>
        <select name="area" class="areaDropdown">
          ${areas.map(a => `<option value="${a.id}">${a.name}</option>`).join('')}
          <option value="__custom__">Other...</option>
        </select>
        <input type="text" name="custom_area" class="customAreaInput" style="display:none;" placeholder="Custom Area" />
      </td>
      <td><input type="text" name="brand" placeholder="Brand" required></td>
      <td>
        <select name="condition" class="conditionDropdown">
          ${statuses.map(s => `<option value="${s.id}">${s.name}</option>`).join('')}
          <option value="__custom__">Other...</option>
        </select>
        <input type="text" name="custom_condition" class="customConditionInput" style="display:none;" placeholder="Custom Condition" />
      </td>
      <td>
        <select name="recommendation">
          <option value="NIL">NIL</option>
          <option value="Replace">Replace</option>
        </select>
      </td>
    `;
    document.getElementById('glass-body').appendChild(row);
    bindRow(row);
  });
});