// ==================== CONFIGURATION ====================
const API_BASE_URL = 'http://localhost:8000';
const RC_URL = 'http://localhost:5000';
const SERVER_URL = 'http://localhost:5001';

// ==================== GLOBAL STATE ====================
let currentUser = null;
let sessionKey = null;
let smartcardData = null;

// ==================== DOM ELEMENTS ====================
// Views
const authView = document.getElementById('auth-view');
const appView = document.getElementById('app-view');

// Auth tabs
const authTabs = document.querySelectorAll('.auth-tab');
const loginPanel = document.getElementById('login-panel');
const registerPanel = document.getElementById('register-panel');

// Forms
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');

// Navigation
const navItems = document.querySelectorAll('.nav-item');
const contentViews = document.querySelectorAll('.content-view');
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar = document.getElementById('sidebar');

// User menu
const userMenuBtn = document.getElementById('user-menu-btn');
const userDropdown = document.getElementById('user-dropdown');
const logoutBtn = document.getElementById('logout-btn');

// Modal
const credentialsModal = document.getElementById('credentials-modal');
const viewCredentialsBtn = document.getElementById('view-credentials-btn');
const closeCredentialsModal = document.getElementById('close-credentials-modal');
const proceedToLoginBtn = document.getElementById('proceed-to-login');
const downloadCredentialsBtn = document.getElementById('download-credentials');

// ==================== UTILITY FUNCTIONS ====================
function showElement(element) {
    if (element) element.style.display = 'block';
}

function hideElement(element) {
    if (element) element.style.display = 'none';
}

function setButtonLoading(button, isLoading, originalText = '') {
    const btnText = button.querySelector('.btn-text');
    const spinner = button.querySelector('.spinner');

    if (isLoading) {
        button.disabled = true;
        if (btnText) btnText.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Processing...';
        if (spinner) spinner.style.display = 'inline-block';
    } else {
        button.disabled = false;
        if (btnText && originalText) btnText.innerHTML = originalText;
        if (spinner) spinner.style.display = 'none';
    }
}

function displayError(container, message) {
    const errorBox = container.querySelector('.error-box') || container;
    const errorMessage = errorBox.querySelector('p') || errorBox;

    if (errorMessage) errorMessage.textContent = message;
    showElement(errorBox);

    setTimeout(() => hideElement(errorBox), 5000);
}

function displaySuccess(container, message) {
    const successBox = container.querySelector('.success-box') || container;
    showElement(successBox);
}

// ==================== AUTH TAB SWITCHING ====================
authTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const targetTab = tab.dataset.tab;

        // Update active tab
        authTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // Show corresponding panel
        if (targetTab === 'login') {
            loginPanel.classList.add('active');
            registerPanel.classList.remove('active');
        } else {
            registerPanel.classList.add('active');
            loginPanel.classList.remove('active');
        }
    });
});

// ==================== REGISTRATION ====================
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const userId = document.getElementById('register-userid').value.trim();
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;
    const submitButton = registerForm.querySelector('button[type="submit"]');

    // Validation
    if (!userId || !password || !confirmPassword) {
        displayError(registerPanel, 'Please fill in all fields');
        return;
    }

    if (password !== confirmPassword) {
        displayError(registerPanel, 'Passwords do not match');
        return;
    }

    if (password.length < 6) {
        displayError(registerPanel, 'Password must be at least 6 characters long');
        return;
    }

    // Hide previous messages
    hideElement(document.getElementById('registration-result'));
    hideElement(document.getElementById('registration-error'));

    setButtonLoading(submitButton, true);

    try {
        const response = await fetch(`${API_BASE_URL}/register_user`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Store smartcard data
            smartcardData = data.SmartCard;

            // Display UID
            document.getElementById('uid-value').textContent = data.UID_i;

            // Store in modal as well
            document.getElementById('modal-wi').textContent = data.SmartCard.W_i;
            document.getElementById('modal-xi').textContent = data.SmartCard.X_i;
            document.getElementById('modal-yi').textContent = data.SmartCard.Y_i;
            document.getElementById('modal-zi').textContent = data.SmartCard.Z_i;
            document.getElementById('modal-ei').textContent = data.SmartCard.E_i;

            showElement(document.getElementById('registration-result'));
            registerForm.reset();
        } else {
            displayError(document.getElementById('registration-error'), data.error || 'Registration failed');
        }
    } catch (error) {
        console.error('Registration error:', error);
        displayError(document.getElementById('registration-error'), 'Network error. Please ensure the middleware server is running.');
    } finally {
        setButtonLoading(submitButton, false, '<i class="fas fa-user-plus"></i> Create Account');
    }
});

// ==================== LOGIN ====================
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const userId = document.getElementById('login-userid').value.trim();
    const password = document.getElementById('login-password').value;
    const submitButton = loginForm.querySelector('button[type="submit"]');

    if (!userId || !password) {
        displayError(document.getElementById('login-error'), 'Please fill in all fields');
        return;
    }

    hideElement(document.getElementById('login-error'));
    setButtonLoading(submitButton, true);

    try {
        const response = await fetch(`${API_BASE_URL}/authenticate_user`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Store session data
            currentUser = userId;
            sessionKey = data.session_key;

            // Update UI with session key
            document.getElementById('current-session-key').textContent = sessionKey;

            // Show app view
            showAppView(userId);

            loginForm.reset();
        } else {
            displayError(document.getElementById('login-error'), data.error || 'Authentication failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        displayError(document.getElementById('login-error'), 'Network error. Please ensure all services are running.');
    } finally {
        setButtonLoading(submitButton, false, '<i class="fas fa-sign-in-alt"></i> Sign In');
    }
});

// ==================== VIEW MANAGEMENT ====================
function showAppView(username) {
    hideElement(authView);
    showElement(appView);

    // Update username in topbar
    document.getElementById('current-user-name').textContent = username;

    // Check system status
    checkSystemStatus();

    // Set up periodic status checks
    setInterval(checkSystemStatus, 30000);
}

function showAuthView() {
    hideElement(appView);
    showElement(authView);

    // Reset state
    currentUser = null;
    sessionKey = null;
    smartcardData = null;
}

// ==================== NAVIGATION ====================
navItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();

        const targetView = item.dataset.view;

        // Update active nav item
        navItems.forEach(nav => nav.classList.remove('active'));
        item.classList.add('active');

        // Show corresponding view
        contentViews.forEach(view => view.classList.remove('active'));
        const viewElement = document.getElementById(`${targetView}-view`);
        if (viewElement) {
            viewElement.classList.add('active');
        }

        // Close sidebar on mobile
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('active');
        }
    });
});

// ==================== SIDEBAR TOGGLE ====================
if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('active');
    });
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768) {
        if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
            sidebar.classList.remove('active');
        }
    }
});

// ==================== USER MENU ====================
if (userMenuBtn) {
    userMenuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        userDropdown.classList.toggle('active');
    });
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    if (userDropdown && !userMenuBtn.contains(e.target)) {
        userDropdown.classList.remove('active');
    }
});

// Logout
if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        showAuthView();
    });
}

// ==================== MODAL HANDLING ====================
if (viewCredentialsBtn) {
    viewCredentialsBtn.addEventListener('click', () => {
        credentialsModal.classList.add('active');
    });
}

if (closeCredentialsModal) {
    closeCredentialsModal.addEventListener('click', () => {
        credentialsModal.classList.remove('active');
    });
}

if (proceedToLoginBtn) {
    proceedToLoginBtn.addEventListener('click', () => {
        credentialsModal.classList.remove('active');
        // Switch to login tab
        authTabs[0].click();
    });
}

// Download credentials
if (downloadCredentialsBtn) {
    downloadCredentialsBtn.addEventListener('click', () => {
        if (!smartcardData) return;

        const data = {
            timestamp: new Date().toISOString(),
            user_credentials: smartcardData
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `smartcard-credentials-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });
}

// Close modal when clicking outside
credentialsModal?.addEventListener('click', (e) => {
    if (e.target === credentialsModal) {
        credentialsModal.classList.remove('active');
    }
});

// ==================== SYSTEM STATUS CHECKING ====================
async function checkSystemStatus() {
    const endpoints = [
        {
            id: 'middleware',
            url: API_BASE_URL,
            badgeId: 'middleware-status-badge',
            textId: 'middleware-status-text'
        },
        {
            id: 'rc',
            url: RC_URL,
            badgeId: 'rc-status-badge',
            textId: 'rc-status-text'
        },
        {
            id: 'server',
            url: SERVER_URL,
            badgeId: 'server-status-badge',
            textId: 'server-status-text'
        }
    ];

    for (const endpoint of endpoints) {
        try {
            const response = await fetch(endpoint.url, {
                method: 'GET',
                mode: 'cors'
            });

            const badgeElement = document.getElementById(endpoint.badgeId);
            const textElement = document.getElementById(endpoint.textId);

            if (badgeElement) {
                const dot = badgeElement.querySelector('.status-dot');
                const text = badgeElement.querySelector('span:last-child');

                if (response.ok) {
                    if (dot) {
                        dot.classList.add('online');
                        dot.classList.remove('offline');
                    }
                    if (text) text.textContent = 'Online';
                } else {
                    throw new Error('Service unavailable');
                }
            }

            if (textElement) {
                textElement.textContent = 'Online and operational';
                textElement.style.color = '#10b981';
            }

            // Get server details if it's the healthcare server
            if (endpoint.id === 'server' && response.ok) {
                const data = await response.json();
                if (data.creds) {
                    const serverIdEl = document.getElementById('server-id');
                    const serverLocEl = document.getElementById('server-location');
                    if (serverIdEl) serverIdEl.textContent = data.creds.ID_j;
                    if (serverLocEl) serverLocEl.textContent = data.creds.Loc_j;
                }
            }
        } catch (error) {
            const badgeElement = document.getElementById(endpoint.badgeId);
            const textElement = document.getElementById(endpoint.textId);

            if (badgeElement) {
                const dot = badgeElement.querySelector('.status-dot');
                const text = badgeElement.querySelector('span:last-child');

                if (dot) {
                    dot.classList.add('offline');
                    dot.classList.remove('online');
                }
                if (text) text.textContent = 'Offline';
            }

            if (textElement) {
                textElement.textContent = 'Service unavailable';
                textElement.style.color = '#ef4444';
            }
        }
    }
}

// Refresh status button
const refreshStatusBtn = document.getElementById('refresh-status');
if (refreshStatusBtn) {
    refreshStatusBtn.addEventListener('click', () => {
        checkSystemStatus();

        // Visual feedback
        const icon = refreshStatusBtn.querySelector('i');
        if (icon) {
            icon.classList.add('fa-spin');
            setTimeout(() => icon.classList.remove('fa-spin'), 1000);
        }
    });
}

// ==================== COPY TO CLIPBOARD ====================
function setupCopyFunctionality() {
    const copyableElements = document.querySelectorAll('.copyable');

    copyableElements.forEach(element => {
        element.style.cursor = 'pointer';
        element.title = 'Click to copy';

        // Remove old listeners by cloning
        const newElement = element.cloneNode(true);
        element.parentNode.replaceChild(newElement, element);

        newElement.addEventListener('click', () => {
            const text = newElement.textContent;

            navigator.clipboard.writeText(text).then(() => {
                const originalText = newElement.textContent;
                const originalBg = newElement.style.background;

                newElement.textContent = '✓ Copied!';
                newElement.style.background = '#dcfce7';

                setTimeout(() => {
                    newElement.textContent = originalText;
                    newElement.style.background = originalBg;
                }, 1500);
            }).catch(err => {
                console.error('Failed to copy:', err);
            });
        });
    });
}

// Initial setup - removed expensive MutationObserver
// Only setup once on page load for better performance
setupCopyFunctionality();

// ==================== INPUT VALIDATION ====================
// Restrict user ID input to alphanumeric and underscore
const userIdInputs = [
    document.getElementById('register-userid'),
    document.getElementById('login-userid')
];

userIdInputs.forEach(input => {
    if (input) {
        input.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/[^a-zA-Z0-9_]/g, '');
        });
    }
});

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    console.log('MediSecure Portal Initialized');

    // Show auth view by default
    showElement(authView);
    hideElement(appView);

    // Initial status check if in app view
    if (currentUser) {
        checkSystemStatus();
    }
});

// ==================== SAMPLE DATA INTERACTIONS ====================
// Use event delegation for better performance - single listener instead of multiple queries
document.body.addEventListener('click', (e) => {
    const btn = e.target.closest('button');
    if (!btn) return;

    const text = btn.textContent;

    // Route button clicks efficiently
    if (text.includes('Book Appointment')) {
        alert('Appointment booking feature coming soon!');
    } else if (text.includes('Upload Record')) {
        alert('Record upload feature coming soon!');
    } else if (text.includes('Request Refill')) {
        alert('Prescription refill request sent!');
    } else if (text.includes('Add Reading')) {
        alert('Add health reading feature coming soon!');
    } else if (text.includes('Make Payment') || text.includes('Pay Now')) {
        alert('Payment processing feature coming soon!');
    } else if (text.includes('Download')) {
        alert('Downloading report...');
    } else if (text.includes('View Details') || (text.includes('View') && !text.includes('Credentials'))) {
        alert('Detailed view coming soon!');
    } else if (text.includes('Export All')) {
        alert('Exporting all lab results...');
    } else if (text.includes('New Message')) {
        alert('Compose message feature coming soon!');
    }
});

// ==================== RESPONSIVE FEATURES ====================
// Handle window resize
let resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        // Remove active class from sidebar on desktop
        if (window.innerWidth > 768) {
            sidebar.classList.remove('active');
        }
    }, 250);
});

// ==================== ERROR HANDLING ====================
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
});

// ==================== SESSION PERSISTENCE (Optional) ====================
// You can implement session storage here if needed
// For now, session only persists during page lifetime

// ==================== NOTIFICATIONS (Placeholder) ====================
const notificationBtn = document.querySelector('.topbar-btn[title="Notifications"]');
if (notificationBtn) {
    notificationBtn.addEventListener('click', () => {
        alert('You have 3 new notifications:\n- Lab results ready\n- Appointment reminder\n- New message from Dr. Johnson');
    });
}

// Messages button
const messagesBtn = document.querySelector('.topbar-btn[title="Messages"]');
if (messagesBtn) {
    messagesBtn.addEventListener('click', () => {
        // Navigate to messages view
        const messagesNavItem = document.querySelector('[data-view="messages"]');
        if (messagesNavItem) messagesNavItem.click();
    });
}

console.log('%c MediSecure Portal ', 'background: #0066cc; color: white; font-size: 16px; padding: 10px; border-radius: 5px;');
console.log('%c Privacy-Preserving Mutual Authentication System ', 'color: #666; font-size: 12px;');
console.log('%c Based on IEEE Access 2020 Research ', 'color: #999; font-size: 10px; font-style: italic;');
