// Copy to Clipboard Functionality
function copyCode() {
    const code = "carlo719460";
    navigator.clipboard.writeText(code).then(() => {
        const btnText = document.getElementById("copyText");
        const originalText = btnText.innerText;
        
        btnText.innerText = "Copied!";
        document.querySelector('.btn-copy').style.borderColor = '#4CAF50';
        document.querySelector('.btn-copy').style.color = '#4CAF50';
        
        setTimeout(() => {
            btnText.innerText = originalText;
            document.querySelector('.btn-copy').style.borderColor = '';
            document.querySelector('.btn-copy').style.color = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}

// Scroll Animation Observer
const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
};

const observer = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('fade-in-up');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.addEventListener('DOMContentLoaded', () => {
    const animatedElements = document.querySelectorAll('.card, .step-item');
    animatedElements.forEach(el => {
        el.style.opacity = '0'; // Initial state
        observer.observe(el);
    });
});
