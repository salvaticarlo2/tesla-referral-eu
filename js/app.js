/**
 * TeslaBlog.eu — App JS
 * Minimal. Only what's needed.
 */

// Generic copy-to-clipboard utility
function copyToClipboard(text, feedbackEl, btnEl, successText) {
  navigator.clipboard.writeText(text).then(function () {
    if (feedbackEl) feedbackEl.textContent = successText || '✓ Copied!';
    if (btnEl) btnEl.classList.add('copied');
    setTimeout(function () {
      if (feedbackEl) feedbackEl.innerHTML = '&nbsp;';
      if (btnEl) btnEl.classList.remove('copied');
    }, 2500);
  }).catch(function () {
    // Fallback for older browsers
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    if (feedbackEl) feedbackEl.textContent = successText || '✓ Copied!';
    setTimeout(function () { if (feedbackEl) feedbackEl.innerHTML = '&nbsp;'; }, 2500);
  });
}
