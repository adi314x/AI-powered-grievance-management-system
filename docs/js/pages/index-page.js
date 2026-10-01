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

    function updateAddressNoticeVisibility() {
        const notice = document.getElementById('addressNotice');
        if (!notice || !state.currentUser) return;

        const missingAddress = (
            !state.currentUser.residential_address
            || !state.currentUser.residential_city
            || !state.currentUser.residential_state
            || !state.currentUser.residential_pincode
        );
        notice.style.display = missingAddress ? 'block' : 'none';
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
            updateAddressNoticeVisibility();

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
