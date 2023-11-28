// -----------------------------Flash messages

window.addEventListener('DOMContentLoaded', (_event) => {
  setTimeout(() => {
    let alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
      new bootstrap.Alert(alert).close();
    });
  }, 5000); // 5000ms = 5 seconds
});


// ------------------------------Text animation

// index title

var titleWrapper = document.querySelector('.title_movement');
titleWrapper.innerHTML = titleWrapper.textContent.replace(/\S/g, "<span class='letter'>$&</span>");

anime.timeline({loop: true})
  .add({
    targets: '.title_movement .letter',
    scale: [4,1],
    opacity: [0,1],
    translateZ: 0,
    easing: "easeOutExpo",
    duration: 950,
    delay: (_el, i) => 70*i
  }).add({
    targets: 'title_movement',
    opacity: 0,
    duration: Infinity,
    easing: "easeOutExpo",
    delay: 1000
  });


// index slogan

var sloganWrapper = document.querySelector('.slogan');
sloganWrapper.innerHTML = sloganWrapper.textContent.replace(/\S/g, "<span class='letter'>$&</span>");

anime.timeline({loop: true})
  .add({
    targets: '.slogan .letter',
    opacity: [0,1],
    easing: "easeInOutQuad",
    duration: 2250,
    delay: (_el, i) => 50 * (i+1)
  }).add({
    targets: '.slogan',
    opacity: 0,
    duration: Infinity,
    easing: "easeOutExpo",
    delay: 1000
  });


// index events

var eventWrapper = document.querySelector('.index_event');
eventWrapper.innerHTML = eventWrapper.textContent.replace(/\S/g, "<span class='letter'>$&</span>");

  anime.timeline({loop: true})
  .add({
    targets: '.index_event .letter',
    translateY: [-100,0],
    easing: "easeOutExpo",
    duration: 1400,
    delay: (_el, i) => 30 * i
  }).add({
    targets: '.index_event',
    opacity: 0,
    duration: 1000,
    easing: "easeOutExpo",
    delay: 1000
  });