

//vehicle form code
document.addEventListener("DOMContentLoaded", function () {
  const dropdowns = [
    { select: "fuelDropdown", input: "customFuelInput" },
    { select: "transmissionDropdown", input: "customTransmissionInput" },
    { select: "engineDropdown", input: "customEngineInput" }
  ];

  dropdowns.forEach(({ select, input }) => {
    const selectElem = document.getElementById(select);
    const inputElem = document.getElementById(input);

    if (selectElem && inputElem) {
      selectElem.addEventListener("change", () => {
        inputElem.style.display = selectElem.value === "__custom__" ? "block" : "none";
        if (selectElem.value !== "__custom__") inputElem.value = "";
      });

      // Trigger once on load in case already selected
      if (selectElem.value === "__custom__") {
        inputElem.style.display = "block";
      }
    }
  });
});

// pramod sir code
const carImageInput = document.getElementById('carImageInput');
    const galleryPreview = document.getElementById('galleryPreview');

    carImageInput.addEventListener('change', (event) => {
      galleryPreview.innerHTML = '';
      Array.from(event.target.files).forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const img = document.createElement('img');
          img.src = e.target.result;
          galleryPreview.appendChild(img);
        }
        reader.readAsDataURL(file);
      });
    });
  document.addEventListener("DOMContentLoaded", () => {
    applySelectColors(); 

    document.querySelectorAll('.status-select').forEach(select => {
      select.addEventListener('change', () => {
        updateSelectColor(select);
      });
    });
  });

  function updateSelectColor(select) {
    const val = select.value;
    if (val === 'notok') {
      select.style.color = 'red';
    } else if (val === 'ok') {
      select.style.color = 'green';
    } else {
      select.style.color = 'black';
    }
  }

  function applySelectColors() {
    document.querySelectorAll('.status-select').forEach(select => {
      updateSelectColor(select);
    });
  }

  function setAll(sectionId, status) {
    const section = document.getElementById(sectionId);
    if (!section) return;

    const selects = section.querySelectorAll('.status-select');
    selects.forEach(select => {
      select.value = status;
      updateSelectColor(select);
    });
  }

  function clearAll(sectionId) {
    const section = document.getElementById(sectionId);
    if (!section) return;

    const selects = section.querySelectorAll('.status-select');
    selects.forEach(select => {
      select.selectedIndex = 0; 
      updateSelectColor(select);
    });

    const inputs = section.querySelectorAll('.issue-input');
    inputs.forEach(input => {
      input.value = '';
    });
  }

// date clander
    function openDatePicker() {
      document.getElementById('hidden-date').click();
    }

    function updateDate() {
      const input = document.getElementById('hidden-date');
      const date = new Date(input.value);
      const options = { month: 'short', year: 'numeric' };
      const formatted = date.toLocaleDateString('en-US', options);
      document.getElementById('date-cell').childNodes[0].nodeValue = formatted + ' ';
    }


  // Create table
  document.getElementById("create").addEventListener("click", function () {
    // Check if input row already exists
    if (document.getElementById("inputRow")) return;

    const tbody = document.getElementById("core");

    // Create input row
    const row = document.createElement("tr");
    row.id = "inputRow";

    row.innerHTML = `
      <td><input type="text" id="newSystem" placeholder="Enter system" /></td>
      <td>
        <select id="newStatus">
          <option value="ok">All OK</option>
          <option value="notok">Not OK</option>
        </select>
      </td>
      <td>
        <input type="number" id="newIssues" min="0" value="0" />
        <button id="saveRow" style="margin-left: 5px; background: green; color: white; border: none; border-radius: 3px;">Save</button>
        <button id="cancelRow" style="margin-left: 5px; background: red; color: white; border: none; border-radius: 3px;">Cancel</button>
      </td>
    `;

    tbody.appendChild(row);

    // Cancel row
    document.getElementById("cancelRow").addEventListener("click", function () {
      row.remove();
    });

    // Save row
    document.getElementById("saveRow").addEventListener("click", function () {
      const system = document.getElementById("newSystem").value.trim();
      const status = document.getElementById("newStatus").value;
      const issues = document.getElementById("newIssues").value;

      if (system === "" || issues === "") {
        alert("Please fill all fields");
        return;
      }

      // Create new row with values
      const newRow = document.createElement("tr");
      newRow.innerHTML = `
        <td>${system}</td>
        <td>
          <select class="status-select">
            <option value="ok" ${status === "ok" ? "selected" : ""}>All OK</option>
            <option value="notok" ${status === "notok" ? "selected" : ""}>Not OK</option>
          </select>
        </td>
        <td>
          <input type="number" class="issue-input" min="0" value="${issues}" />
        </td>
      `;

      tbody.replaceChild(newRow, row); // Replace input row with actual data row
    });
  });

// sensor
  
  document.getElementById("create-sensor").addEventListener("click", function () {
    // Prevent multiple input rows
    if (document.getElementById("inputRow")) return;

    const tbody = document.getElementById("sensor");

    // Create input row
    const row = document.createElement("tr");
    row.id = "inputRow";

    row.innerHTML = `
      <td><input type="text" id="newArea" placeholder="Enter area" /></td>
      <td>
        <select id="newRemark">
          <option value="ok">All System OK</option>
          <option value="notok">Not OK</option>
        </select>
        <button id="saveRow" style="margin-left: 5px; background: green; color: white; border: none; border-radius: 3px;">Save</button>
        <button id="cancelRow" style="margin-left: 5px; background: red; color: white; border: none; border-radius: 3px;">Cancel</button>
      </td>
    `;

    tbody.appendChild(row);

    // Cancel row
    document.getElementById("cancelRow").addEventListener("click", function () {
      row.remove();
    });

    // Save row
    document.getElementById("saveRow").addEventListener("click", function () {
      const area = document.getElementById("newArea").value.trim();
      const remark = document.getElementById("newRemark").value;

      if (area === "") {
        alert("Please enter an area name.");
        return;
      }

      // Create new row with values
      const newRow = document.createElement("tr");
      newRow.innerHTML = `
        <td>${area}</td>
        <td>
          <select class="status-select">
            <option value="ok" ${remark === "ok" ? "selected" : ""}>All System OK</option>
            <option value="notok" ${remark === "notok" ? "selected" : ""}>Not OK</option>
          </select>
        </td>
      `;

      tbody.replaceChild(newRow, row); // Replace input row with actual data row
    });
  });



  
  document.addEventListener("DOMContentLoaded", function () {
  // ---------- PART 2: OTHER CHECKS ----------
  const otherChecksBtn = document.getElementById("other-checks");
  const otherChecksTable = document.getElementById("other-checks-table").querySelector("tbody");

  otherChecksBtn.addEventListener("click", function () {
    const newRow = document.createElement("tr");
    newRow.innerHTML = `
      <td contenteditable="true">New Check</td>
      <td>
        <select>
          <option>OK</option>
          <option>Not OK</option>
        </select>
      </td>
      <td><input type="text" value="NIL" /></td>
      <td>
        <button class="save-btn" style="color: green;">Save</button>
        <button class="cancel-btn" style="color: red;">Cancel</button>
      </td>
    `;
    otherChecksTable.appendChild(newRow);

    newRow.querySelector(".save-btn").addEventListener("click", function () {
      newRow.children[0].contentEditable = "false";
      newRow.children[2].querySelector("input").readOnly = true;
      newRow.removeChild(newRow.children[3]);
    });

    newRow.querySelector(".cancel-btn").addEventListener("click", function () {
      otherChecksTable.removeChild(newRow);
    });
  });



  // ---------- PART 1: LIVE PARAMETERS ----------
  const liveCreateBtn = document.getElementById("create-live");
  const liveTable = liveCreateBtn.nextElementSibling.nextElementSibling.querySelector("tbody");

  liveCreateBtn.addEventListener("click", function () {
    const newRow = document.createElement("tr");
    newRow.innerHTML = `
      <td contenteditable="true">New Parameter</td>
      <td contenteditable="true">--</td>
      <td>
        <select>
          <option>OK</option>
          <option>Not OK</option>
        </select>
      </td>
      <td><input type="text" value="NIL" /></td>
      <td colspan="4" style="text-align: right; padding-top: 5px;">
        <button class="save-btn" style="color: green; margin-right: 10px;">Save</button>
        <button class="cancel-btn" style="color: red;">Cancel</button>
      </td>
    `;
    liveTable.appendChild(newRow);

    newRow.querySelector(".save-btn").addEventListener("click", function () {
      newRow.children[0].contentEditable = "false";
      newRow.children[1].contentEditable = "false";
      newRow.children[3].querySelector("input").readOnly = true;
      newRow.removeChild(newRow.children[4]);
    });

    newRow.querySelector(".cancel-btn").addEventListener("click", function () {
      liveTable.removeChild(newRow);
    });
  });
});

// ---------- Fluid-lavels--------------//
document.addEventListener("DOMContentLoaded", function () {
  const fluidBtn = document.getElementById("Fluid-levels");
  const fluidTableBody = fluidBtn.closest("section").querySelector("tbody");

  fluidBtn.addEventListener("click", function () {
    // Main editable data row
    const newRow = document.createElement("tr");
    newRow.innerHTML = `
      <td contenteditable="true">New Fluid</td>
      <td contenteditable="true">In Range</td>
      <td>
        <select>
          <option>OK</option>
          <option>Contaminated</option>
          <option>Damaged</option>
          <option>Leak Found</option>
        </select>
      </td>
      <td><input type="text" value="NIL" /></td>
    `;

    // Action buttons row below
    const actionRow = document.createElement("tr");
    actionRow.innerHTML = `
      <td colspan="4" style="text-align: right; padding-top: 5px;">
        <button class="save-btn" style="color: green; margin-right: 10px;">Save</button>
        <button class="cancel-btn" style="color: red;">Cancel</button>
      </td>
    `;

    // Append both rows
    fluidTableBody.appendChild(newRow);
    fluidTableBody.appendChild(actionRow);

    // Save logic
    actionRow.querySelector(".save-btn").addEventListener("click", function () {
      newRow.children[0].contentEditable = "false";
      newRow.children[1].contentEditable = "false";
      newRow.children[3].querySelector("input").readOnly = true;
      fluidTableBody.removeChild(actionRow); // remove buttons
    });

    // Cancel logic
    actionRow.querySelector(".cancel-btn").addEventListener("click", function () {
      fluidTableBody.removeChild(newRow);
      fluidTableBody.removeChild(actionRow);
    });
  });
});

// --------------Fit-Finish----------------//
document.addEventListener("DOMContentLoaded", function () {
  const fitBtn = document.getElementById("Fit-Finish");
  const fitSection = fitBtn.closest(".section");
  const fitTableBody = fitSection.querySelector("tbody");

  fitBtn.addEventListener("click", function () {
    const newRow = document.createElement("tr");

    newRow.innerHTML = `
      <td contenteditable="true">New Area</td>
      <td>
        <select>
          <option>No</option>
          <option>Yes</option>
        </select>
      </td>
      <td>
        <select>
          <option>All OK</option>
          <option>Not OK</option>
        </select>
      </td>
      <td contenteditable="true">NIL</td>
    `;

    const actionRow = document.createElement("tr");
    actionRow.innerHTML = `
      <td colspan="4" style="text-align: right; padding-top: 5px;">
        <button class="save-btn" style="color: white; background-color: green; padding: 5px 12px; border-radius: 4px; border: none; margin-right: 10px;">Save</button>
        <button class="cancel-btn" style="color: white; background-color: red; padding: 5px 12px; border-radius: 4px; border: none;">Cancel</button>
      </td>
    `;

    fitTableBody.appendChild(newRow);
    fitTableBody.appendChild(actionRow);

    // Save button logic
    actionRow.querySelector(".save-btn").addEventListener("click", function () {
      newRow.querySelectorAll("td").forEach(td => td.contentEditable = "false");
      newRow.querySelectorAll("select").forEach(select => select.disabled = true);
      fitTableBody.removeChild(actionRow);
    });

    // Cancel button logic
    actionRow.querySelector(".cancel-btn").addEventListener("click", function () {
      fitTableBody.removeChild(newRow);
      fitTableBody.removeChild(actionRow);
    });
  });
});


// ----------------Flush-gap---------------------//
document.addEventListener("DOMContentLoaded", function () {
  const flushBtn = document.getElementById("Flush-gaps");
  const flushTableBody = flushBtn.closest("section") 
    ? flushBtn.closest("section").querySelector("tbody")
    : flushBtn.closest("div").querySelector("tbody");

  flushBtn.addEventListener("click", function () {
    const newRow = document.createElement("tr");

    newRow.innerHTML = `
      <td contenteditable="true">New Area</td>
      <td contenteditable="true">Smooth</td>
      <td>
        <select>
          <option>No</option>
          <option>Yes</option>
        </select>
      </td>
      <td>
        <select>
          <option>NIL</option>
          <option>Adjust</option>
        </select>
      </td>
    `;

    const actionRow = document.createElement("tr");
    actionRow.innerHTML = `
      <td colspan="4" style="text-align: right; padding-top: 5px;">
        <button class="save-btn" style="color: white; background-color: green; padding: 5px 12px; border-radius: 4px; border: none; margin-right: 10px;">Save</button>
        <button class="cancel-btn" style="color: white; background-color: red; padding: 5px 12px; border-radius: 4px; border: none;">Cancel</button>
      </td>
    `;

    flushTableBody.appendChild(newRow);
    flushTableBody.appendChild(actionRow);

    // Save logic
    actionRow.querySelector(".save-btn").addEventListener("click", function () {
      newRow.querySelectorAll("td[contenteditable]").forEach(td => td.contentEditable = "false");
      newRow.querySelectorAll("select").forEach(select => select.disabled = true);
      flushTableBody.removeChild(actionRow);
    });

    // Cancel logic
    actionRow.querySelector(".cancel-btn").addEventListener("click", function () {
      flushTableBody.removeChild(newRow);
      flushTableBody.removeChild(actionRow);
    });
  });
});



// ------------- Critical-Rubber-------------------//

document.addEventListener("DOMContentLoaded", function () {
  const rubberBtn = document.getElementById("Critical-Rubber");
  
  // यहीं पर सही टेबल को पकड़ो: बटन के बाद वाला table
  const rubberTableBody = rubberBtn.nextElementSibling.querySelector("tbody");

  rubberBtn.addEventListener("click", function () {
    const newRow = document.createElement("tr");
    newRow.innerHTML = `
      <td contenteditable="true">New Area</td>
      <td>
        <select>
          <option>All OK</option>
          <option>Not OK</option>
        </select>
      </td>
      <td>
        <select>
          <option>NIL</option>
          <option>Replace</option>
        </select>
      </td>
    `;

    const actionRow = document.createElement("tr");
    actionRow.innerHTML = `
      <td colspan="3" style="text-align: right; padding-top: 5px;">
        <button class="save-btn" style="color: white; background-color: green; padding: 5px 12px; border-radius: 4px; border: none; margin-right: 10px;">Save</button>
        <button class="cancel-btn" style="color: white; background-color: red; padding: 5px 12px; border-radius: 4px; border: none;">Cancel</button>
      </td>
    `;

    rubberTableBody.appendChild(newRow);
    rubberTableBody.appendChild(actionRow);

    actionRow.querySelector(".save-btn").addEventListener("click", function () {
      newRow.querySelector("td[contenteditable]").contentEditable = "false";
      newRow.querySelectorAll("select").forEach(sel => sel.disabled = true);
      rubberTableBody.removeChild(actionRow);
    });

    actionRow.querySelector(".cancel-btn").addEventListener("click", function () {
      rubberTableBody.removeChild(newRow);
      rubberTableBody.removeChild(actionRow);
    });
  });
});


// ---------------------- condition-of-glass------------//
document.addEventListener("DOMContentLoaded", function () {
  const glassBtn = document.getElementById("Condition-of-class");

  // टेबल का tbody पकड़ो — यह बटन के बाद वाला टेबल है
  const glassTableBody = glassBtn.nextElementSibling.querySelector("tbody");

  glassBtn.addEventListener("click", function () {
    // नया row बनाएँ
    const newRow = document.createElement("tr");
    newRow.innerHTML = `
      <td contenteditable="true">New Area</td>
      <td contenteditable="true">Brand</td>
      <td>
        <select>
          <option>All OK</option>
          <option>Not OK</option>
        </select>
      </td>
      <td>
        <select>
          <option>NIL</option>
          <option>Replace</option>
        </select>
      </td>
    `;

    // Save / Cancel वाले extra row बनाएँ
    const actionRow = document.createElement("tr");
    actionRow.innerHTML = `
      <td colspan="4" style="text-align: right; padding-top: 5px;">
        <button class="save-btn" style="color: white; background-color: green; padding: 5px 12px; border-radius: 4px; border: none; margin-right: 10px;">Save</button>
        <button class="cancel-btn" style="color: white; background-color: red; padding: 5px 12px; border-radius: 4px; border: none;">Cancel</button>
      </td>
    `;

    // दोनों rows टेबल में जोड़ो
    glassTableBody.appendChild(newRow);
    glassTableBody.appendChild(actionRow);

    // Save बटन पर क्लिक होने पर contenteditable बंद और select disable हो जाए
    actionRow.querySelector(".save-btn").addEventListener("click", function () {
      newRow.querySelectorAll("td[contenteditable]").forEach(td => td.contentEditable = "false");
      newRow.querySelectorAll("select").forEach(sel => sel.disabled = true);
      glassTableBody.removeChild(actionRow);
    });

    // Cancel बटन पर क्लिक होने पर दोनों rows हटा दो
    actionRow.querySelector(".cancel-btn").addEventListener("click", function () {
      glassTableBody.removeChild(newRow);
      glassTableBody.removeChild(actionRow);
    });
  });
});


// ----------------------- Floor-Carpets -----------------------//
document.addEventListener("DOMContentLoaded", function () {
  const carpetBtn = document.getElementById("Floor-Carpets");

  // बटन के बाद जो पहला <table> है, उसका tbody पकड़ें
  const carpetTableBody = carpetBtn.closest("h4").nextElementSibling.querySelector("tbody");

  carpetBtn.addEventListener("click", function () {
    // नया input row
    const newRow = document.createElement("tr");
    newRow.innerHTML = `
      <td contenteditable="true">New Area</td>
      <td>
        <select>
          <option>Present</option>
          <option>Not Present</option>
        </select>
      </td>
      <td>
        <select>
          <option>All OK</option>
          <option>Not OK</option>
        </select>
      </td>
      <td contenteditable="true">OK</td>
    `;

    // Save / Cancel row
    const actionRow = document.createElement("tr");
    actionRow.innerHTML = `
      <td colspan="4" style="text-align: right; padding-top: 5px;">
        <button class="save-btn" style="color: white; background-color: green; padding: 5px 12px; border-radius: 4px; border: none; margin-right: 10px;">Save</button>
        <button class="cancel-btn" style="color: white; background-color: red; padding: 5px 12px; border-radius: 4px; border: none;">Cancel</button>
      </td>
    `;

    // टेबल में जोड़ें
    carpetTableBody.appendChild(newRow);
    carpetTableBody.appendChild(actionRow);

    // Save बटन: select disable और contenteditable हटा दो
    actionRow.querySelector(".save-btn").addEventListener("click", function () {
      newRow.querySelectorAll("td[contenteditable]").forEach(td => td.contentEditable = "false");
      newRow.querySelectorAll("select").forEach(sel => sel.disabled = true);
      carpetTableBody.removeChild(actionRow);
    });

    // Cancel बटन: दोनों rows हटाओ
    actionRow.querySelector(".cancel-btn").addEventListener("click", function () {
      carpetTableBody.removeChild(newRow);
      carpetTableBody.removeChild(actionRow);
    });
  });
});


// ----------------------- Plastic-Panels ------------------------- //
document.addEventListener("DOMContentLoaded", function () {
  const plasticBtn = document.getElementById("Plastic-Panels");

  // बटन के बाद वाला पहला <table> पकड़ना
  const plasticTableBody = plasticBtn.closest("h4").nextElementSibling.querySelector("tbody");

  plasticBtn.addEventListener("click", function () {
    // नया row बनाना
    const newRow = document.createElement("tr");
    newRow.innerHTML = `
      <td contenteditable="true">New Area</td>
      <td>
        <select>
          <option>All OK</option>
          <option>Not OK</option>
        </select>
      </td>
      <td contenteditable="true">OK</td>
    `;

    // Action row - Save / Cancel
    const actionRow = document.createElement("tr");
    actionRow.innerHTML = `
      <td colspan="3" style="text-align: right; padding-top: 5px;">
        <button class="save-btn" style="color: white; background-color: green; padding: 5px 12px; border-radius: 4px; border: none; margin-right: 10px;">Save</button>
        <button class="cancel-btn" style="color: white; background-color: red; padding: 5px 12px; border-radius: 4px; border: none;">Cancel</button>
      </td>
    `;

    // टेबल में जोड़ना
    plasticTableBody.appendChild(newRow);
    plasticTableBody.appendChild(actionRow);

    // Save बटन क्लिक -> disable editable और select को
    actionRow.querySelector(".save-btn").addEventListener("click", function () {
      newRow.querySelectorAll("td[contenteditable]").forEach(td => td.contentEditable = "false");
      newRow.querySelectorAll("select").forEach(sel => sel.disabled = true);
      plasticTableBody.removeChild(actionRow);
    });

    // Cancel बटन क्लिक -> दोनों row हटाना
    actionRow.querySelector(".cancel-btn").addEventListener("click", function () {
      plasticTableBody.removeChild(newRow);
      plasticTableBody.removeChild(actionRow);
    });
  });
});


// -------------------- Fabric-Leather ----------------------------//


document.addEventListener("DOMContentLoaded", function () {
  const createButton = document.getElementById("Fabric-Leather");
  const fabricTableBody = document.querySelector("#fabric-table tbody");

  createButton.addEventListener("click", function () {
    const newRow = document.createElement("tr");

    // Area input
    const areaCell = document.createElement("td");
    const areaInput = document.createElement("input");
    areaInput.type = "text";
    areaInput.placeholder = "Enter Area";
    areaCell.appendChild(areaInput);
    newRow.appendChild(areaCell);

    // Condition select
    const conditionCell = document.createElement("td");
    const conditionSelect = document.createElement("select");
    ["All OK", "Not OK", "NA"].forEach(text => {
      const opt = document.createElement("option");
      opt.text = text;
      conditionSelect.add(opt);
    });
    conditionCell.appendChild(conditionSelect);
    newRow.appendChild(conditionCell);

    // Recommendation input
    const recCell = document.createElement("td");
    const recInput = document.createElement("input");
    recInput.type = "text";
    recInput.value = "OK";
    recCell.appendChild(recInput);
    newRow.appendChild(recCell);

    // Empty placeholder for Action column
    const emptyActionCell = document.createElement("td");
    newRow.appendChild(emptyActionCell);

    // Add row
    fabricTableBody.appendChild(newRow);

    // Below row: Save/Cancel buttons row
    const actionRow = document.createElement("tr");
    const actionCell = document.createElement("td");
    actionCell.colSpan = 4;
    actionCell.style.textAlign = "right";

    // Save Button
    const saveBtn = document.createElement("button");
    saveBtn.textContent = "Save";
    saveBtn.style.marginRight = "10px";
    saveBtn.style.backgroundColor = "green";
    saveBtn.style.color = "white";
    saveBtn.style.border = "none";
    saveBtn.style.padding = "5px 10px";
    saveBtn.style.borderRadius = "4px";
    saveBtn.style.cursor = "pointer";

    // Cancel Button
    const cancelBtn = document.createElement("button");
    cancelBtn.textContent = "Cancel";
    cancelBtn.style.backgroundColor = "gray";
    cancelBtn.style.color = "white";
    cancelBtn.style.border = "none";
    cancelBtn.style.padding = "5px 10px";
    cancelBtn.style.borderRadius = "4px";
    cancelBtn.style.cursor = "pointer";

    // Save: Replace inputs with text
    saveBtn.addEventListener("click", () => {
      areaCell.textContent = areaInput.value;
      conditionCell.textContent = conditionSelect.value;
      recCell.textContent = recInput.value;
      actionRow.remove();
    });

    // Cancel: Remove both rows
    cancelBtn.addEventListener("click", () => {
      newRow.remove();
      actionRow.remove();
    });

    actionCell.appendChild(saveBtn);
    actionCell.appendChild(cancelBtn);
    actionRow.appendChild(actionCell);
    fabricTableBody.appendChild(actionRow);
  });
});



// -------------------------- Vehicle-Documentation -------------------------//
document.addEventListener("DOMContentLoaded", function () {
  const createBtn = document.getElementById("Vehicle-Documentation");
  const tableBody = createBtn.nextElementSibling.querySelector("tbody");

  createBtn.addEventListener("click", function () {
    const newRow = document.createElement("tr");

    // System input
    const systemCell = document.createElement("td");
    const systemInput = document.createElement("input");
    systemInput.type = "text";
    systemInput.placeholder = "Enter System";
    systemInput.style.width = "100%";
    systemCell.appendChild(systemInput);
    newRow.appendChild(systemCell);

    // Status select
    const statusCell = document.createElement("td");
    const statusSelect = document.createElement("select");
    ["All OK", "NIL"].forEach(status => {
      const opt = document.createElement("option");
      opt.textContent = status;
      statusSelect.appendChild(opt);
    });
    statusCell.appendChild(statusSelect);
    newRow.appendChild(statusCell);

    // Remark input
    const remarkCell = document.createElement("td");
    const remarkInput = document.createElement("input");
    remarkInput.type = "text";
    remarkInput.placeholder = "Enter Remark";
    remarkInput.style.width = "100%";
    remarkCell.appendChild(remarkInput);
    newRow.appendChild(remarkCell);

    // Append new editable row
    tableBody.appendChild(newRow);

    // Add Save/Cancel buttons row
    const actionRow = document.createElement("tr");
    const actionCell = document.createElement("td");
    actionCell.colSpan = 3;
    actionCell.style.textAlign = "right";
    actionCell.style.paddingTop = "10px";

    const saveBtn = document.createElement("button");
    saveBtn.textContent = "Save";
    saveBtn.style.backgroundColor = "green";
    saveBtn.style.color = "white";
    saveBtn.style.border = "none";
    saveBtn.style.padding = "6px 12px";
    saveBtn.style.marginRight = "10px";
    saveBtn.style.borderRadius = "4px";
    saveBtn.style.cursor = "pointer";

    const cancelBtn = document.createElement("button");
    cancelBtn.textContent = "Cancel";
    cancelBtn.style.backgroundColor = "gray";
    cancelBtn.style.color = "white";
    cancelBtn.style.border = "none";
    cancelBtn.style.padding = "6px 12px";
    cancelBtn.style.borderRadius = "4px";
    cancelBtn.style.cursor = "pointer";

    // Save logic
    saveBtn.addEventListener("click", () => {
      systemCell.textContent = systemInput.value || "N/A";
      statusCell.textContent = statusSelect.value;
      remarkCell.textContent = remarkInput.value || "NIL";
      actionRow.remove();
    });

    // Cancel logic
    cancelBtn.addEventListener("click", () => {
      newRow.remove();
      actionRow.remove();
    });

    actionCell.appendChild(saveBtn);
    actionCell.appendChild(cancelBtn);
    actionRow.appendChild(actionCell);
    tableBody.appendChild(actionRow);
  });
});
