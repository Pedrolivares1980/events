// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function () {
  // Get references to the checkbox and the company name container
  const isBusinessCheckbox = document.getElementById('is_business');
  const companyNameContainer = document.getElementById('company_name_container');

  // Function to toggle the display of the company name field
  function toggleCompanyNameField() {
    // If the checkbox is checked, show the company name field
    if (isBusinessCheckbox.checked) {
      companyNameContainer.style.display = 'block';
    } else {
      // Otherwise, hide it
      companyNameContainer.style.display = 'none';
    }
  }

  // Add a change event listener to the checkbox
  isBusinessCheckbox.addEventListener('change', toggleCompanyNameField);

  // Call the function initially to set the correct state of the company name field
  toggleCompanyNameField();
});
