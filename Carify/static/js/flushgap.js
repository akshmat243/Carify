document.addEventListener("DOMContentLoaded", function () {
  const flushAreas = JSON.parse(document.getElementById('flush-areas-data').textContent);
  const operations = JSON.parse(document.getElementById('operations-data').textContent);

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
    bindDropdown(row.querySelector('select.operationDropdown'), row.querySelector('input.customOperationInput'));
  }

  document.querySelectorAll('#flush-body tr').forEach(bindRow);

  document.getElementById('Flush-gaps').addEventListener('click', function () {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>
        <select name="area" class="areaDropdown">
          ${flushAreas.map(a => `<option value="${a.id}">${a.name}</option>`).join('')}
          <option value="__custom__">Other...</option>
        </select>
        <input type="text" name="custom_area" placeholder="Custom area" class="customAreaInput" style="display: none;" />
      </td>
      <td>
        <select name="operation" class="operationDropdown">
          ${operations.map(o => `<option value="${o.id}">${o.name}</option>`).join('')}
          <option value="__custom__">Other...</option>
        </select>
        <input type="text" name="custom_operation" placeholder="Custom operation" class="customOperationInput" style="display: none;" />
      </td>
      <td>
        <select name="observation">
          <option value="Yes">Yes</option>
          <option value="No">No</option>
        </select>
      </td>
      <td>
        <select name="action">
          <option>NIL</option>
          <option>Adjust</option>
        </select>
      </td>
    `;
    document.getElementById('flush-body').appendChild(row);
    bindRow(row);
  });
});