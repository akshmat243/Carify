 document.addEventListener('DOMContentLoaded', function () {
    const areas = JSON.parse(document.getElementById('areas-data').textContent);
    const statuses = JSON.parse(document.getElementById('statuses-data').textContent);

    const areaOptions = areas.map(a => `<option value="${a.id}">${a.name}</option>`).join('');
    const statusOptions = statuses.map(s => `<option value="${s.id}">${s.name}</option>`).join('');

    function setupDynamicDropdown(select, input) {
      if (!select || !input) return;
      select.addEventListener('change', function () {
        input.style.display = this.value === '__custom__' ? 'block' : 'none';
        if (this.value !== '__custom__') input.value = '';
      });
      if (select.value === '__custom__') input.style.display = 'block';
    }

    function bindDropdowns(row) {
      setupDynamicDropdown(row.querySelector('select.areaDropdown'), row.querySelector('input.customAreaInput'));
      setupDynamicDropdown(row.querySelector('select.statusDropdown'), row.querySelector('input.customStatusInput'));
    }

    document.querySelectorAll('#sensor tr').forEach(bindDropdowns);

    document.getElementById('create_network').addEventListener('click', function (e) {
      e.preventDefault();

      const tbody = document.getElementById('sensor');
      const newRow = document.createElement('tr');
      newRow.innerHTML = `
        <td>
          <select name="area" class="areaDropdown">
            ${areaOptions}
            <option value="__custom__">Other...</option>
          </select>
          <input type="text" name="custom_area" class="customAreaInput" placeholder="Enter custom area" style="display: none; margin-top: 5px;" />
        </td>
        <td>
          <select name="status" class="statusDropdown">
            ${statusOptions}
            <option value="__custom__">Other...</option>
          </select>
          <input type="text" name="custom_status" class="customStatusInput" placeholder="Enter custom status" style="display: none; margin-top: 5px;" />
        </td>
        <td><input type="text" name="remark" class="issue-input" /></td>
      `;
      tbody.appendChild(newRow);
      bindDropdowns(newRow);
    });
  });