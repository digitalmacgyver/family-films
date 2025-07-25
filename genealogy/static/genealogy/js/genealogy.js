// Genealogy App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeGenealogyFeatures();
});

function initializeGenealogyFeatures() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Initialize person search functionality
    initializePersonSearch();
    
    // Initialize form enhancements
    initializeFormEnhancements();
    
    // Initialize tree navigation
    initializeTreeNavigation();
}

// Person Search Functionality
function initializePersonSearch() {
    const searchInputs = document.querySelectorAll('.person-search');
    
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length < 2) {
                hideSearchResults(this);
                return;
            }
            
            searchTimeout = setTimeout(() => {
                searchPeople(query, this);
            }, 300);
        });
        
        // Hide results when clicking outside
        document.addEventListener('click', function(e) {
            if (!input.contains(e.target)) {
                hideSearchResults(input);
            }
        });
    });
}

function searchPeople(query, inputElement) {
    // This would typically make an AJAX call to the search API
    // For now, we'll implement a placeholder
    
    const resultsContainer = getOrCreateResultsContainer(inputElement);
    resultsContainer.innerHTML = '<div class="search-loading">Searching...</div>';
    
    // Simulate API call
    setTimeout(() => {
        // In a real implementation, this would be the API response
        const mockResults = [
            { id: 1, name: 'John Doe', birth_year: '1950' },
            { id: 2, name: 'Jane Smith', birth_year: '1955' }
        ];
        
        displaySearchResults(mockResults, resultsContainer, inputElement);
    }, 500);
}

function getOrCreateResultsContainer(inputElement) {
    let container = inputElement.parentNode.querySelector('.search-results');
    
    if (!container) {
        container = document.createElement('div');
        container.className = 'search-results';
        container.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #dee2e6;
            border-top: none;
            border-radius: 0 0 0.375rem 0.375rem;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        `;
        
        inputElement.parentNode.style.position = 'relative';
        inputElement.parentNode.appendChild(container);
    }
    
    return container;
}

function displaySearchResults(results, container, inputElement) {
    if (results.length === 0) {
        container.innerHTML = '<div class="search-no-results p-2 text-muted">No people found</div>';
        return;
    }
    
    const html = results.map(person => `
        <div class="search-result-item p-2 border-bottom" data-person-id="${person.id}" style="cursor: pointer;">
            <div class="fw-bold">${person.name}</div>
            ${person.birth_year ? `<small class="text-muted">Born ${person.birth_year}</small>` : ''}
        </div>
    `).join('');
    
    container.innerHTML = html;
    
    // Add click handlers
    container.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', function() {
            const personId = this.dataset.personId;
            const personName = this.querySelector('.fw-bold').textContent;
            
            // Update the input or select field
            if (inputElement.tagName === 'SELECT') {
                // For select fields, we'd need to add the option if it doesn't exist
                selectPersonInDropdown(inputElement, personId, personName);
            } else {
                inputElement.value = personName;
                inputElement.dataset.personId = personId;
            }
            
            hideSearchResults(inputElement);
        });
        
        // Hover effects
        item.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.backgroundColor = 'white';
        });
    });
}

function selectPersonInDropdown(selectElement, personId, personName) {
    // Check if option already exists
    let option = selectElement.querySelector(`option[value="${personId}"]`);
    
    if (!option) {
        option = document.createElement('option');
        option.value = personId;
        option.textContent = personName;
        selectElement.appendChild(option);
    }
    
    selectElement.value = personId;
}

function hideSearchResults(inputElement) {
    const container = inputElement.parentNode.querySelector('.search-results');
    if (container) {
        container.remove();
    }
}

// Form Enhancements
function initializeFormEnhancements() {
    // Auto-save for biography forms
    const biographyTextareas = document.querySelectorAll('textarea[name="notes"]');
    biographyTextareas.forEach(textarea => {
        let autoSaveTimeout;
        let lastSavedContent = textarea.value;
        
        textarea.addEventListener('input', function() {
            clearTimeout(autoSaveTimeout);
            
            autoSaveTimeout = setTimeout(() => {
                if (this.value !== lastSavedContent) {
                    autoSaveBiography(this);
                    lastSavedContent = this.value;
                }
            }, 5000); // Auto-save after 5 seconds of inactivity
        });
    });
    
    // Form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateGenealogyForm(this)) {
                e.preventDefault();
                return false;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Saving...';
                submitBtn.disabled = true;
                
                // Re-enable if form submission fails
                setTimeout(() => {
                    if (submitBtn.disabled) {
                        submitBtn.innerHTML = originalText;
                        submitBtn.disabled = false;
                    }
                }, 10000);
            }
        });
    });
}

function autoSaveBiography(textarea) {
    const indicator = getOrCreateAutoSaveIndicator(textarea);
    indicator.textContent = 'Saving...';
    indicator.className = 'auto-save-indicator text-muted small';
    
    // In a real implementation, this would make an AJAX call
    setTimeout(() => {
        indicator.textContent = 'Draft saved';
        indicator.className = 'auto-save-indicator text-success small';
        
        setTimeout(() => {
            indicator.textContent = '';
        }, 3000);
    }, 1000);
}

function getOrCreateAutoSaveIndicator(textarea) {
    let indicator = textarea.parentNode.querySelector('.auto-save-indicator');
    
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'auto-save-indicator';
        textarea.parentNode.appendChild(indicator);
    }
    
    return indicator;
}

function validateGenealogyForm(form) {
    // Basic validation for genealogy forms
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    // Validate relationship logic
    const fatherSelect = form.querySelector('select[name="father"]');
    const motherSelect = form.querySelector('select[name="mother"]');
    const spouseSelect = form.querySelector('select[name="spouse"]');
    const personId = form.dataset.personId;
    
    if (fatherSelect && fatherSelect.value === personId) {
        showFieldError(fatherSelect, 'A person cannot be their own father');
        isValid = false;
    }
    
    if (motherSelect && motherSelect.value === personId) {
        showFieldError(motherSelect, 'A person cannot be their own mother');
        isValid = false;
    }
    
    if (spouseSelect && spouseSelect.value === personId) {
        showFieldError(spouseSelect, 'A person cannot be their own spouse');
        isValid = false;
    }
    
    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('is-invalid');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Tree Navigation
function initializeTreeNavigation() {
    // Keyboard navigation for tree
    document.addEventListener('keydown', function(e) {
        if (e.target.closest('.family-tree-container')) {
            handleTreeKeyNavigation(e);
        }
    });
    
    // Touch/swipe support for mobile
    initializeTouchNavigation();
}

function handleTreeKeyNavigation(e) {
    const focusedElement = document.activeElement;
    const treePersons = document.querySelectorAll('.tree-person');
    
    if (!focusedElement.classList.contains('tree-person')) {
        return;
    }
    
    let currentIndex = Array.from(treePersons).indexOf(focusedElement);
    let newIndex = currentIndex;
    
    switch(e.key) {
        case 'ArrowLeft':
            newIndex = Math.max(0, currentIndex - 1);
            break;
        case 'ArrowRight':
            newIndex = Math.min(treePersons.length - 1, currentIndex + 1);
            break;
        case 'Enter':
        case ' ':
            focusedElement.click();
            e.preventDefault();
            return;
    }
    
    if (newIndex !== currentIndex) {
        treePersons[newIndex].focus();
        e.preventDefault();
    }
}

function initializeTouchNavigation() {
    const treeContainer = document.querySelector('.family-tree-container');
    if (!treeContainer) return;
    
    let touchStartX = 0;
    let touchStartY = 0;
    
    treeContainer.addEventListener('touchstart', function(e) {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
    }, { passive: true });
    
    treeContainer.addEventListener('touchend', function(e) {
        if (!touchStartX || !touchStartY) return;
        
        const touchEndX = e.changedTouches[0].clientX;
        const touchEndY = e.changedTouches[0].clientY;
        
        const diffX = touchStartX - touchEndX;
        const diffY = touchStartY - touchEndY;
        
        // Determine swipe direction
        if (Math.abs(diffX) > Math.abs(diffY)) {
            if (Math.abs(diffX) > 50) { // Minimum swipe distance
                if (diffX > 0) {
                    // Swipe left - could navigate to next person
                    navigateTreeDirection('next');
                } else {
                    // Swipe right - could navigate to previous person
                    navigateTreeDirection('prev');
                }
            }
        }
        
        touchStartX = 0;
        touchStartY = 0;
    }, { passive: true });
}

function navigateTreeDirection(direction) {
    // This would implement tree navigation logic
    console.log('Tree navigation:', direction);
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for use in other scripts
window.GenealogyApp = {
    searchPeople,
    autoSaveBiography,
    validateGenealogyForm,
    debounce,
    throttle
};