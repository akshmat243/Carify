document.addEventListener('DOMContentLoaded', function () {
  const docs = JSON.parse(document.getElementById('doc-types-data').textContent);
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
    bindDropdown(row.querySelector('select.documentDropdown'), row.querySelector('input.customDocumentInput'));
    bindDropdown(row.querySelector('select.statusDropdown'), row.querySelector('input.customStatusInput'));
  }

  document.querySelectorAll('#doc-body tr').forEach(bindRow);

  document.getElementById('Vehicle-Documentation').addEventListener('click', function () {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>
        <select name="document" class="documentDropdown">
          ${docs.map(d => `<option value="${d.id}">${d.name}</option>`).join('')}
          <option value="__custom__">Other...</option>
        </select>
        <input type="text" name="custom_document" class="customDocumentInput" style="display:none;" placeholder="Custom Document" />
      </td>
      <td>
        <select name="status" class="statusDropdown">
          ${statuses.map(s => `<option value="${s.id}">${s.name}</option>`).join('')}
          <option value="__custom__">Other...</option>
        </select>
        <input type="text" name="custom_status" class="customStatusInput" style="display:none;" placeholder="Custom Status" />
      </td>
      <td><input type="text" name="remark" placeholder="Remark"></td>
    `;
    document.getElementById('doc-body').appendChild(row);
    bindRow(row);
  });
});
