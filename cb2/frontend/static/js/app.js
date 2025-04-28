/**
 * Carbon Black Multi-Tenant Console - Common JavaScript
 */

// Global app object
const CBApp = {
    // API endpoints
    api: {
        instances: '/api/instances/',
        agents: '/api/agents/',
        sync: '/api/sync/',
        licenses: '/api/licenses/',
        cb_users: '/api/cb-users/',
        import: '/api/import/'
    },
    
    // Common functions
    utils: {
        /**
         * Format a date string
         * @param {string} dateStr - Date string to format
         * @returns {string} Formatted date string or null if invalid
         */
        formatDate: function(dateStr) {
            if (!dateStr) return null;
            
            try {
                const date = new Date(dateStr);
                return date.toLocaleString();
            } catch (e) {
                return dateStr;
            }
        },
        
        /**
         * Escape HTML special characters
         * @param {string} str - String to escape
         * @returns {string} Escaped string
         */
        escapeHtml: function(str) {
            if (!str) return '';
            return str
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        },
        
        /**
         * Show an alert message
         * @param {string} type - Alert type (success, danger, warning, info)
         * @param {string} message - Alert message
         * @param {number} timeout - Auto-dismiss timeout in ms (default: 5000)
         */
        showAlert: function(type, message, timeout = 5000) {
            const alertHtml = `
                <div class="alert alert-${type} alert-dismissible alert-floating fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
            
            $('#alertContainer').append(alertHtml);
            
            // Auto dismiss after timeout
            setTimeout(function() {
                $('.alert-floating').alert('close');
            }, timeout);
        },
        
        /**
         * Debounce function execution
         * @param {function} func - Function to debounce
         * @param {number} wait - Wait time in ms
         * @returns {function} Debounced function
         */
        debounce: function(func, wait) {
            let timeout;
            return function(...args) {
                const context = this;
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(context, args), wait);
            };
        }
    },
    
    // Load common components
    init: function() {
        // Add event listeners for common components
        $(document).ready(function() {
            // Initialize tooltips
            $('[data-bs-toggle="tooltip"]').tooltip();
            
            // Handle sidebar toggle on mobile
            $('.sidebar-toggle').on('click', function() {
                $('.sidebar').toggleClass('show');
            });
        });
    }
};

// Initialize the app
$(document).ready(function() {
    CBApp.init();
}); 