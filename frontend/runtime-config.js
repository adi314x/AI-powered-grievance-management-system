(function initRuntimeConfig(globalScope) {
    const config = globalScope.APP_RUNTIME_CONFIG || {};

    function readOptionalLocalStorage(key) {
        try {
            if (!globalScope.localStorage) return '';
            return globalScope.localStorage.getItem(key) || '';
        } catch {
            return '';
        }
    }

    function normalizeBase(input) {
        return (input || '').trim().replace(/\/+$/, '');
    }

    const configuredBase = normalizeBase(config.apiBaseUrl);
    const metaBase = normalizeBase(
        document.querySelector('meta[name="app-api-base-url"]')?.getAttribute('content') || ''
    );
    const localStorageBase = normalizeBase(readOptionalLocalStorage('app_api_base_url'));

    let apiBase = configuredBase || metaBase || localStorageBase;
    if (!apiBase) {
        if ((globalScope.location?.hostname || '').endsWith('github.io')) {
            apiBase = 'https://smart-grievance-system.onrender.com/api';
        } else {
            apiBase = `${globalScope.location?.origin || ''}/api`;
        }
    }

    apiBase = normalizeBase(apiBase);

    globalScope.APP_RUNTIME_CONFIG = {
        ...config,
        apiBaseUrl: apiBase,
    };

    globalScope.getApiBaseUrl = function getApiBaseUrl() {
        return apiBase;
    };

    globalScope.resolveApiUrl = function resolveApiUrl(path) {
        const normalizedPath = path.startsWith('/') ? path : `/${path}`;
        if (normalizedPath === '/api' || normalizedPath.startsWith('/api/')) {
            return `${apiBase}${normalizedPath.slice(4)}`;
        }
        return `${apiBase}${normalizedPath}`;
    };
})(window);
