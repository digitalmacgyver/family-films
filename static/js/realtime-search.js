// Real-time search functionality
(function() {
    'use strict';
    
    let searchTimeout;
    const SEARCH_DELAY = 300; // milliseconds to wait before searching
    
    function initRealtimeSearch() {
        const searchInput = document.querySelector('input[name="q"]');
        const searchForm = searchInput ? searchInput.closest('form') : null;
        
        if (!searchInput || !searchForm) {
            return;
        }
        
        // Remove the submit button to indicate real-time search
        const submitButton = searchForm.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.style.display = 'none';
        }
        
        // Add loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'spinner-border spinner-border-sm text-light ms-2';
        loadingIndicator.style.display = 'none';
        loadingIndicator.setAttribute('role', 'status');
        loadingIndicator.innerHTML = '<span class="visually-hidden">Loading...</span>';
        searchInput.parentElement.appendChild(loadingIndicator);
        
        // Handle input events
        searchInput.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            
            const query = e.target.value.trim();
            
            // Show loading indicator
            loadingIndicator.style.display = 'inline-block';
            
            // Delay search to avoid too many requests
            searchTimeout = setTimeout(() => {
                performSearch(query, loadingIndicator);
            }, SEARCH_DELAY);
        });
        
        // Prevent form submission on enter
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = searchInput.value.trim();
            performSearch(query, loadingIndicator);
        });
    }
    
    function performSearch(query, loadingIndicator) {
        // Update URL without page reload
        const newUrl = new URL(window.location);
        if (query) {
            newUrl.searchParams.set('q', query);
        } else {
            newUrl.searchParams.delete('q');
        }
        window.history.pushState({}, '', newUrl);
        
        // If on search page, update results
        if (window.location.pathname.includes('/search/')) {
            updateSearchResults(query, loadingIndicator);
        } else {
            // Navigate to search page
            window.location.href = `/search/?q=${encodeURIComponent(query)}`;
        }
    }
    
    function updateSearchResults(query, loadingIndicator) {
        // Add AJAX parameter to request
        const searchUrl = new URL(window.location);
        searchUrl.searchParams.set('ajax', '1');
        if (query) {
            searchUrl.searchParams.set('q', query);
        } else {
            searchUrl.searchParams.delete('q');
        }
        
        fetch(searchUrl.toString(), {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(html => {
            // Parse the response and update the content
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Update the results container
            const resultsContainer = document.querySelector('.search-results');
            const newResults = doc.querySelector('.search-results');
            
            if (resultsContainer && newResults) {
                resultsContainer.innerHTML = newResults.innerHTML;
                
                // Re-initialize any dynamic content
                initializeDynamicContent();
            }
            
            // Hide loading indicator
            loadingIndicator.style.display = 'none';
        })
        .catch(error => {
            console.error('Search error:', error);
            loadingIndicator.style.display = 'none';
        });
    }
    
    function initializeDynamicContent() {
        // Re-initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.forEach(function (tooltipTriggerEl) {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Re-initialize animated thumbnails if present
        if (typeof initializeAnimatedThumbnails === 'function') {
            initializeAnimatedThumbnails();
        }
    }
    
    // Initialize on DOM load
    document.addEventListener('DOMContentLoaded', initRealtimeSearch);
})();