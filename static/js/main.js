// Main JavaScript for AI Quant Analyst

document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const tickerInput = document.getElementById('ticker');
            if (tickerInput && tickerInput.value.trim() === '') {
                e.preventDefault();
                alert('Please enter a stock ticker');
                return false;
            }
            
            // Show loading state
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Analyzing...';
            }
        });
    }
    
    // File upload validation
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const allowedTypes = ['application/pdf', 'text/plain'];
                if (!allowedTypes.includes(file.type)) {
                    alert('Please select a PDF or text file');
                    e.target.value = '';
                    return;
                }
                
                const maxSize = 16 * 1024 * 1024; // 16MB
                if (file.size > maxSize) {
                    alert('File size must be less than 16MB');
                    e.target.value = '';
                    return;
                }
            }
        });
    }
    
    // Flash message auto-hide
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });
});

// Utility functions
function showLoading() {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.style.display = 'block';
    }
}

function hideLoading() {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
}

function updateProgress(progress) {
    const progressBar = document.getElementById('progress-fill');
    if (progressBar) {
        progressBar.style.width = progress + '%';
    }
}