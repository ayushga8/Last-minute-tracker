/**
 * Last-Minute Life Saver — Main JavaScript
 * Dark mode toggle, countdown timers, AJAX habits, sidebar toggle
 */

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initCountdownTimers();
    initMobileSidebar();
    initAlertAutoDismiss();
});

/* ============================================
   THEME TOGGLE
   ============================================ */
function initThemeToggle() {
    const toggle = document.getElementById('themeToggle');
    const html = document.documentElement;

    // Load saved preference
    const saved = localStorage.getItem('theme');
    if (saved) {
        html.setAttribute('data-theme', saved);
    }

    if (toggle) {
        toggle.addEventListener('click', () => {
            const current = html.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
        });
    }
}

/* ============================================
   COUNTDOWN TIMERS
   ============================================ */
function initCountdownTimers() {
    const countdowns = document.querySelectorAll('.task-countdown[data-deadline]');
    if (countdowns.length === 0) return;

    function updateCountdowns() {
        const now = new Date();
        countdowns.forEach(el => {
            const deadline = new Date(el.dataset.deadline);
            const diff = deadline - now;
            const display = el.querySelector('.countdown-value');
            if (!display) return;

            if (diff <= 0) {
                display.textContent = 'OVERDUE';
                display.style.color = '#ef4444';
                return;
            }

            const days = Math.floor(diff / 86400000);
            const hours = Math.floor((diff % 86400000) / 3600000);
            const minutes = Math.floor((diff % 3600000) / 60000);
            const seconds = Math.floor((diff % 60000) / 1000);

            if (days > 0) {
                display.textContent = `${days}d ${hours}h`;
            } else if (hours > 0) {
                display.textContent = `${hours}h ${minutes}m`;
                if (hours <= 2) display.style.color = '#f97316';
            } else if (minutes > 0) {
                display.textContent = `${minutes}m ${seconds}s`;
                display.style.color = '#ef4444';
            } else {
                display.textContent = `${seconds}s`;
                display.style.color = '#ef4444';
                display.style.fontWeight = '900';
            }
        });
    }

    updateCountdowns();
    setInterval(updateCountdowns, 1000);
}

/* ============================================
   MOBILE SIDEBAR
   ============================================ */
function initMobileSidebar() {
    const btn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');

    if (btn && sidebar) {
        btn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (sidebar.classList.contains('open') &&
                !sidebar.contains(e.target) &&
                !btn.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }
}

/* ============================================
   AUTO-DISMISS ALERTS
   ============================================ */
function initAlertAutoDismiss() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.animation = 'slideUp 0.3s ease forwards';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}

// SlideUp animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideUp {
        to { opacity: 0; transform: translateY(-8px); height: 0; padding: 0; margin: 0; overflow: hidden; }
    }
`;
document.head.appendChild(style);

/* ============================================
   AJAX HABIT MARK DONE
   ============================================ */
document.querySelectorAll('.mark-done-form').forEach(form => {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const action = form.action;
        const csrf = form.querySelector('[name=csrfmiddlewaretoken]').value;

        try {
            const resp = await fetch(action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrf,
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });
            const data = await resp.json();

            if (data.success) {
                // Update UI
                const card = form.closest('.habit-card');
                if (card) {
                    card.classList.add('habit-done');
                    const streakNum = card.querySelector('.streak-number');
                    if (streakNum) streakNum.textContent = data.streak;

                    // Replace button with done badge
                    form.outerHTML = '<span class="done-badge">✅ Done Today</span>';

                    // Flash animation
                    card.style.transform = 'scale(1.02)';
                    setTimeout(() => { card.style.transform = ''; }, 200);
                }
            }
        } catch (err) {
            // Fallback to normal form submission
            form.submit();
        }
    });
});
