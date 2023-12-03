// -----------------------------Flash messages

window.addEventListener('DOMContentLoaded', (_event) => {
  setTimeout(() => {
    let alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
      new bootstrap.Alert(alert).close();
    });
  }, 5000); // 5000ms = 5 seconds
});
