/**
 * Road Transportation Expert System - Main Client-side JS
 */

document.addEventListener('DOMContentLoaded', function () {
    // Mobile Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const appSidebar = document.querySelector('.app-sidebar');

    if (sidebarToggle && appSidebar) {
        sidebarToggle.addEventListener('click', function () {
            appSidebar.classList.toggle('show');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function (e) {
            if (window.innerWidth < 992) {
                if (!appSidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                    appSidebar.classList.remove('show');
                }
            }
        });
    }

    // Assessment Form Submission Spinner
    const assessmentForm = document.getElementById('assessmentForm');
    const analyzeBtn = document.getElementById('analyzeBtn');

    if (assessmentForm && analyzeBtn) {
        assessmentForm.addEventListener('submit', function (e) {
            // Show loading state
            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Evaluating Knowledge Base...
            `;
        });
    }

    // Reset Button handling
    const resetBtn = document.getElementById('resetFormBtn');
    if (resetBtn && assessmentForm) {
        resetBtn.addEventListener('click', function (e) {
            e.preventDefault();
            assessmentForm.reset();
            // Clear any error states
            const errorFeedbacks = assessmentForm.querySelectorAll('.invalid-feedback');
            errorFeedbacks.forEach(el => el.style.display = 'none');
            const isInvalids = assessmentForm.querySelectorAll('.is-invalid');
            isInvalids.forEach(el => el.classList.remove('is-invalid'));
        });
    }

    // Initialize Bootstrap tooltips if any
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
