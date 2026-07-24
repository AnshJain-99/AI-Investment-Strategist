document.addEventListener("DOMContentLoaded", () => {

    // Animate all progress bars
    document.querySelectorAll("[data-width]").forEach(el => {
        el.style.width = el.dataset.width + "%";
    });

});