
 document.addEventListener('DOMContentLoaded', function () {
    let currentStep = 1;
    const totalSteps = 3;

    const nextBtn = document.getElementById('nextBtn');
    const prevBtn = document.getElementById('prevBtn');
    const submitBtn = document.getElementById('submitBtn');

    function updateFormStep() {
      for (let i = 1; i <= totalSteps; i++) {
        const step = document.getElementById(`step-${i}`);
        const indicator = document.getElementById(`step-indicator-${i}`);
        if (step) step.classList.remove('active');
        if (indicator) indicator.classList.remove('active');
      }

      document.getElementById(`step-${currentStep}`).classList.add('active');
      document.getElementById(`step-indicator-${currentStep}`).classList.add('active');

      prevBtn.style.display = currentStep === 1 ? 'none' : 'inline-block';
      nextBtn.style.display = currentStep === totalSteps ? 'none' : 'inline-block';
      submitBtn.classList.toggle('d-none', currentStep !== totalSteps);
    }

    if (nextBtn) nextBtn.addEventListener('click', () => {
      if (currentStep < totalSteps) {
        currentStep++;
        updateFormStep();
      }
    });

    if (prevBtn) prevBtn.addEventListener('click', () => {
      if (currentStep > 1) {
        currentStep--;
        updateFormStep();
      }
    });

    updateFormStep();

    // Profile image preview
    const profileInput = document.getElementById('id_profile_picture');
    const previewImg = document.getElementById('profilePreview');
    if (profileInput && previewImg) {
      profileInput.addEventListener('change', function (e) {
        const file = e.target.files[0];
        if (file) {
          previewImg.src = URL.createObjectURL(file);
        }
      });
    }

    // Bank Verification AJAX
    const verifyBtn = document.getElementById("verifyBankBtn");
    if (verifyBtn) {
      verifyBtn.addEventListener("click", function () {
        const account = document.getElementById("id_bank_account_number").value;
        const ifsc = document.getElementById("id_ifsc_code").value;

        fetch("{% url 'verify_bank' %}", {
          method: "POST",
          headers: {
            "X-CSRFToken": "{{ csrf_token }}",
            "Content-Type": "application/x-www-form-urlencoded"
          },
          body: new URLSearchParams({
            account_number: account,
            ifsc_code: ifsc
          })
        })
        .then(res => res.json())
        .then(data => {
          alert(data.message);
        });
      });
    }
  });
