(function initCitizenHomePage(globalScope) {
    const state = {
        currentUser: null,
    };

    function showAlert(message, type = 'info') {
        const alertBox = document.getElementById('alertBox');
        if (!alertBox) return;

        alertBox.textContent = message;
        alertBox.className = `alert ${type}`;
        alertBox.style.display = 'block';

        if (type !== 'info') {
            setTimeout(() => {
                alertBox.style.display = 'none';
            }, 5000);
        }
    }

    function handleRoleRedirect(user) {
        if (user.role === 'ADMIN') {
            window.location.href = 'admin.html';
            return true;
        }
        if (user.role === 'OFFICER') {
            window.location.href = 'officer.html';
            return true;
        }
        return false;
    }

    async function checkAuthAndInitialize() {
        try {
            const data = await apiCall('/auth/me');
            state.currentUser = data.user;

            if (handleRoleRedirect(state.currentUser)) {
                return;
            }

            const welcome = document.getElementById('userWelcome');
            if (welcome) {
                welcome.textContent = `Welcome, ${state.currentUser.name}`;
            }

            // Soft reminder — no restriction, just a heads-up
            const u = state.currentUser;
            if (!u.residential_address || !u.residential_city || !u.residential_state || !u.residential_pincode) {
                showAlert('Your profile is not completed. You can still submit grievances, but completing your profile helps faster processing.', 'info');
            }

            if (globalScope.CitizenGrievanceForm) {
                globalScope.CitizenGrievanceForm.initialize({
                    currentUser: state.currentUser,
                    showAlert,
                    onSubmitted: async () => {
                        if (globalScope.CitizenDashboardWidgets) {
                            await globalScope.CitizenDashboardWidgets.refreshDashboard();
                        }
                    },
                });
            }

            if (globalScope.CitizenDashboardWidgets) {
                await globalScope.CitizenDashboardWidgets.refreshDashboard();
            }
        } catch (error) {
            window.location.href = 'login.html';
        }
    }

    function bindGlobalActions() {
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => logout());
        }

        // Mobile logout button mirrors the desktop one
        const logoutBtnMobile = document.getElementById('logoutBtnMobile');
        if (logoutBtnMobile) {
            logoutBtnMobile.addEventListener('click', () => logout());
        }

        // Hamburger menu toggle
        const hamburger = document.getElementById('navHamburger');
        const mobileNav = document.getElementById('mobileNav');
        if (hamburger && mobileNav) {
            hamburger.addEventListener('click', () => {
                const isOpen = mobileNav.classList.toggle('open');
                hamburger.setAttribute('aria-expanded', String(isOpen));
            });
        }
    }

    function boot() {
        bindGlobalActions();
        checkAuthAndInitialize();
    }

    globalScope.CitizenIndexPage = {
        boot,
        showAlert,
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})(window);
