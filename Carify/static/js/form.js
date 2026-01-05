document.getElementById('btn').addEventListener('click', function () {
  const name = document.getElementById('name').value;
  const email = document.getElementById('email').value;
  const phone = document.getElementById('phone').value;

  const formData = new FormData();
  formData.append('name', name);
  formData.append('email', email);
  formData.append('phone_number', phone); // use field names matching your Django form

  fetch('/carify/form/customer/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCSRFToken(),
    },
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert(data.message);
        window.location.href = data.next_url; // redirect to vehicle form
      } else {
        alert('Error: ' + JSON.stringify(data.errors));
      }
    })
    .catch((error) => console.error('Error:', error));
});

// Helper function to fetch CSRF token from cookies
function getCSRFToken() {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const c = cookie.trim();
    if (c.startsWith(name + '=')) {
      return c.substring(name.length + 1);
    }
  }
  return '';
}

