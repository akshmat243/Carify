document.addEventListener('DOMContentLoaded', function () {
  const systems = JSON.parse(document.getElementById('systems-data').textContent);
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

  function bindDropdownsInRow(row) {
    setupDynamicDropdown(row.querySelector('select.systemDropdown'), row.querySelector('input.customSystemInput'));
    setupDynamicDropdown(row.querySelector('select.statusDropdown'), row.querySelector('input.customStatusInput'));
  }

  document.querySelectorAll('#core tr').forEach(bindDropdownsInRow);

  const createBtn = document.getElementById('create1');
  if (createBtn) {
    createBtn.addEventListener('click', function (e) {
      e.preventDefault();
      const tbody = document.getElementById('core');
      const newRow = document.createElement('tr');

      newRow.innerHTML = `
        <td>
          <select name="system" class="systemDropdown">
            ${systemOptions}
            <option value="__custom__">Other...</option>
          </select>
          <input type="text" name="custom_system" class="customSystemInput" placeholder="Enter custom system" style="display:none;" />
        </td>
        <td>
          <select name="status" class="statusDropdown">
            ${statusOptions}
            <option value="__custom__">Other...</option>
          </select>
          <input type="text" name="custom_status" class="customStatusInput" placeholder="Enter custom status" style="display:none;" />
        </td>
        <td>
          <input type="number" name="number_of_issues" value="0" min="0" />
        </td>
      `;

      tbody.appendChild(newRow);
      bindDropdownsInRow(newRow);
    });
  }
});


// static/js/vehicle_autofill.js

document.addEventListener("DOMContentLoaded", function () {
  const vinInput = document.getElementById("id_vin");

  if (!vinInput) return;

  vinInput.addEventListener("change", function () {
    const vin = vinInput.value.trim();

    if (!vin || vin.length < 5) return;

    // Show a loading message
    console.log("Fetching data for VIN:", vin);

    // 🔍 NHTSA vPIC - Airbags & Basic Info
    fetch(`https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/${vin}?format=json`)
      .then(response => response.json())
      .then(data => {
        const result = data.Results[0];
        let airbagCount = 0;
        const airbagKeys = Object.keys(result).filter(key => key.includes("AirBagLoc"));
        airbagKeys.forEach(key => {
          if (result[key] && result[key].toLowerCase() !== 'not applicable') {
            airbagCount++;
          }
        });

        const airbagField = document.getElementById("id_auto_airbags");
        if (airbagField) airbagField.value = airbagCount;

        console.log("Airbags:", airbagCount);
      })
      .catch(error => console.error("vPIC error:", error));

    // 🚗 CarAPI - Performance & Mileage
    fetch(`https://api.api-ninjas.com/v1/cars?vin=${vin}`, {
      method: 'GET',
      headers: {
        'X-Api-Key': '5H3EeO//mvhT/lOGxMIf3Q==PUTE2hXe43BvtrXm'
      }
    })
      .then(res => res.json())
      .then(data => {
        const car = Array.isArray(data) ? data[0] : data;
        if (!car) return;

        const bhpField = document.getElementById("id_auto_bhp");
        const cityMpgField = document.getElementById("id_auto_city_mpg");
        const highwayMpgField = document.getElementById("id_auto_highway_mpg");

        if (car.horsepower_hp && bhpField) bhpField.value = car.horsepower_hp;
        if (car.city_mpg && cityMpgField) cityMpgField.value = car.city_mpg;
        if (car.highway_mpg && highwayMpgField) highwayMpgField.value = car.highway_mpg;

        console.log("Fetched CarAPI:", car);
      })
      .catch(error => console.error("CarAPI error:", error));
  });
});
