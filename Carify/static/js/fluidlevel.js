document.addEventListener('DOMContentLoaded', function () {
  // Get dropdown data from <script type="application/json"> blocks
  const areas = JSON.parse(document.getElementById('fluid-areas-data').textContent);
  const ranges = JSON.parse(document.getElementById('fluid-ranges-data').textContent);
  const statuses = JSON.parse(document.getElementById('statuses-data').textContent);

  // Handles visibility of custom input fields
  function bindDropdown(select, input) {
    if (!select || !input) return;

    // Set initial visibility
    if (select.value === '__custom__') {
      input.style.display = 'block';
    } else {
      input.style.display = 'none';
      input.value = '';
    }

    // Listen for changes
    select.addEventListener('change', function () {
      if (this.value === '__custom__') {
        input.style.display = 'block';
      } else {
        input.style.display = 'none';
        input.value = '';
      }
    });
  }

  // Binds logic to a single table row
  function bindRow(row) {
    bindDropdown(row.querySelector('select.areaDropdown'), row.querySelector('input.customAreaInput'));
    bindDropdown(row.querySelector('select.rangeDropdown'), row.querySelector('input.customRangeInput'));
    bindDropdown(row.querySelector('select.statusDropdown'), row.querySelector('input.customStatusInput'));
  }

  // Bind all existing rows on page load
  document.querySelectorAll('#fluid-body tr').forEach(bindRow);

  // Handle "Create" button to add new row
  const createBtn = document.getElementById('fluid-create');
  if (createBtn) {
    createBtn.addEventListener('click', function () {
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
          <select name="in_range" class="rangeDropdown">
            ${ranges.map(r => `<option value="${r.id}">${r.name}</option>`).join('')}
            <option value="__custom__">Other...</option>
          </select>
          <input type="text" name="custom_range" class="customRangeInput" placeholder="Enter custom range" style="display:none;" />
        </td>
        <td>
          <select name="contamination" class="statusDropdown">
            ${statuses.map(s => `<option value="${s.id}">${s.name}</option>`).join('')}
            <option value="__custom__">Other...</option>
          </select>
          <input type="text" name="custom_status" class="customStatusInput" placeholder="Enter custom status" style="display:none;" />
        </td>
        <td><input type="text" name="recommendation" value="NIL" /></td>
      `;
      document.getElementById('fluid-body').appendChild(row);
      bindRow(row);
    });
  }
});
