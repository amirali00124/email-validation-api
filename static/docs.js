document.addEventListener('DOMContentLoaded', function() {
    // API Tester functionality
    const apiTestForm = document.getElementById('api-test-form');
    const apiTestResult = document.getElementById('api-test-result');
    const apiTestOutput = document.getElementById('api-test-output');

    if (apiTestForm) {
        apiTestForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const apiKey = document.getElementById('api-key').value;
            const email = document.getElementById('test-email').value;
            
            if (!apiKey || !email) {
                alert('Please enter both API key and email address');
                return;
            }
            
            // Show loading state
            apiTestOutput.textContent = 'Testing API...';
            apiTestResult.style.display = 'block';
            
            try {
                const response = await fetch('/api/validate', {
                    method: 'POST',
                    headers: {
                        'X-API-Key': apiKey,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email: email })
                });
                
                const result = await response.json();
                
                // Format and display result
                apiTestOutput.textContent = JSON.stringify(result, null, 2);
                
                // Add status indicator
                if (response.ok) {
                    apiTestOutput.className = 'bg-dark p-3 rounded border border-success';
                } else {
                    apiTestOutput.className = 'bg-dark p-3 rounded border border-danger';
                }
                
            } catch (error) {
                apiTestOutput.textContent = JSON.stringify({
                    error: 'Request failed: ' + error.message
                }, null, 2);
                apiTestOutput.className = 'bg-dark p-3 rounded border border-danger';
            }
        });
    }
    
    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('a[href^="#"]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Update active state in navigation
                updateActiveNavLink(this);
            }
        });
    });
    
    // Update active navigation link based on scroll position
    window.addEventListener('scroll', function() {
        updateActiveNavOnScroll();
    });
    
    function updateActiveNavLink(activeLink) {
        const navItems = document.querySelectorAll('.list-group-item-action');
        navItems.forEach(item => {
            item.classList.remove('active');
        });
        activeLink.classList.add('active');
    }
    
    function updateActiveNavOnScroll() {
        const sections = document.querySelectorAll('section[id]');
        const navLinks = document.querySelectorAll('.list-group-item-action');
        
        let current = '';
        
        sections.forEach(section => {
            const sectionTop = section.getBoundingClientRect().top;
            if (sectionTop <= 100) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active');
            }
        });
    }
    
    // Copy code block functionality
    const codeBlocks = document.querySelectorAll('.code-block');
    codeBlocks.forEach(block => {
        // Add copy button
        const copyButton = document.createElement('button');
        copyButton.className = 'btn btn-sm btn-outline-secondary position-absolute top-0 end-0 m-2';
        copyButton.innerHTML = '<i class="fas fa-copy"></i>';
        copyButton.title = 'Copy to clipboard';
        
        // Make the parent relative for absolute positioning
        block.style.position = 'relative';
        block.appendChild(copyButton);
        
        copyButton.addEventListener('click', function() {
            const code = block.querySelector('code').textContent;
            navigator.clipboard.writeText(code).then(() => {
                // Show success feedback
                const originalHTML = copyButton.innerHTML;
                copyButton.innerHTML = '<i class="fas fa-check text-success"></i>';
                copyButton.classList.remove('btn-outline-secondary');
                copyButton.classList.add('btn-outline-success');
                
                setTimeout(() => {
                    copyButton.innerHTML = originalHTML;
                    copyButton.classList.remove('btn-outline-success');
                    copyButton.classList.add('btn-outline-secondary');
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy: ', err);
            });
        });
    });
    
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Search functionality for documentation
    const searchInput = document.getElementById('doc-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const sections = document.querySelectorAll('.documentation-content section');
            
            sections.forEach(section => {
                const text = section.textContent.toLowerCase();
                if (text.includes(searchTerm) || searchTerm === '') {
                    section.style.display = 'block';
                } else {
                    section.style.display = 'none';
                }
            });
        });
    }
});

// Utility function to format JSON responses
function formatApiResponse(response, isError = false) {
    const className = isError ? 'border-danger' : 'border-success';
    return `<pre class="bg-dark p-3 rounded border ${className}">${JSON.stringify(response, null, 2)}</pre>`;
}

// Utility function to validate email format on client side
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Export functions for use in other scripts if needed
window.EmailValidatorDocs = {
    formatApiResponse,
    isValidEmail
};
