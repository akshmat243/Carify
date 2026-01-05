

document.addEventListener('DOMContentLoaded', function () {
  const areas = JSON.parse(document.getElementById('paint-areas-data').textContent);
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

  document.querySelectorAll('#paint-body tr').forEach(bindRow);

  document.getElementById('paint-create').addEventListener('click', function () {
    const row = document.createElement('tr');
    row.innerHTML = `
  <td>
    <select name="area" class="areaDropdown">
      ${areas.map(a => `<option value="${a.id}">${a.name}</option>`).join('')}
      <option value="__custom__">Other...</option>
    </select>
    <input type="text" name="custom_area" class="customAreaInput" placeholder="Enter custom area" style="display:none;" />
  </td>
  <td>
    <input type="hidden" name="repainted" value="off">
    <label>
      <input type="checkbox" name="repainted" value="on">
      Repainted?
    </label>
  </td>
  <td>
    <select name="condition" class="conditionDropdown">
      ${statuses.map(s => `<option value="${s.id}">${s.name}</option>`).join('')}
      <option value="__custom__">Other...</option>
    </select>
    <input type="text" name="custom_condition" class="customConditionInput" placeholder="Enter custom condition" style="display:none;" />
  </td>
  <td><input type="text" name="action" value="NIL" /></td>
`;

    document.getElementById('paint-body').appendChild(row);
    bindRow(row);
  });
});
