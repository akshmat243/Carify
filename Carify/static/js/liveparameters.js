document.addEventListener('DOMContentLoaded', function () {
  const parameters = JSON.parse(document.getElementById('parameters-data').textContent);
  const inferences = JSON.parse(document.getElementById('inferences-data').textContent);

  const paramOptions = parameters.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
  const infOptions = inferences.map(i => `<option value="${i.id}">${i.name}</option>`).join('');

  function setupDropdown(select, input) {
    if (!select || !input) return;
    select.addEventListener('change', function () {
      input.style.display = this.value === '__custom__' ? 'block' : 'none';
      if (this.value !== '__custom__') input.value = '';
    });
    if (select.value === '__custom__') input.style.display = 'block';
  }

  function bindRowEvents(row) {
    setupDropdown(row.querySelector('select.systemDropdown'), row.querySelector('input.customSystemInput'));
    setupDropdown(row.querySelector('select.inferenceDropdown'), row.querySelector('input.customInferenceInput'));
  }

  document.querySelectorAll('#live-body tr').forEach(bindRowEvents);

  document.getElementById('create-live').addEventListener('click', function (e) {
    e.preventDefault();
    const tbody = document.getElementById('live-body');
    const newRow = document.createElement('tr');
    newRow.innerHTML = `
      <td>
        <select name="system" class="systemDropdown">
          ${paramOptions}
          <option value="__custom__">Other...</option>
        </select>
        <input type="text" name="custom_system" class="customSystemInput" placeholder="Enter custom system" style="display:none;" />
      </td>
      <td>
        <select name="inference" class="inferenceDropdown">
          ${infOptions}
          <option value="__custom__">Other...</option>
        </select>
        <input type="text" name="custom_inference" class="customInferenceInput" placeholder="Enter custom inference" style="display:none;" />
      </td>
    `;
    tbody.appendChild(newRow);
    bindRowEvents(newRow);
  });
});
