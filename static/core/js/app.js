function () {
    const toggles = document.querySelectorAll("[data-sidebar-toggle]");
    const sidebar = document.getElementById("sidebar");

    toggles.forEach(btn => {
        btn.addEventListener("click", () => {
            if (!sidebar) return;
            sidebar.classList.toggle("open");
        });
    });

    // Click outside to close on mobile
    document.addEventListener("click", (e) => {
        if (!sidebar) return;
        const isOpen = sidebar.classList.contains("open");
        if (!isOpen) return;

        const clickedToggle = e.target.closest("[data-sidebar-toggle]");
        const clickedInsideSidebar = e.target.closest("#sidebar");
        if (!clickedToggle && !clickedInsideSidebar) {
            sidebar.classList.remove("open");
        }
    });
}();