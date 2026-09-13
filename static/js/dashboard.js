// DevBlog Dashboard Interaction Scripts

document.addEventListener('DOMContentLoaded', () => {
    // 1. Sidebar toggle for mobile devices
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('dashboardSidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('is-active');
        });
    }

    // 2. Destructive delete confirmation helper
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const message = btn.getAttribute('data-confirm-delete') || 'Are you sure you want to proceed with this deletion? This cannot be undone.';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
});
