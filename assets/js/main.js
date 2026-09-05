/**
 * Conscious Brain Lab - Main JavaScript
 * Handles Dark/Light Mode, Mobile Navigation, and Global UI Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Theme Management (Dark / Light Mode)
  const themeToggleBtn = document.getElementById('theme-toggle');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const savedTheme = localStorage.getItem('cbl-theme');

  const currentTheme = savedTheme || (prefersDark ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', currentTheme);
  updateThemeIcon(currentTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const activeTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('cbl-theme', newTheme);
      updateThemeIcon(newTheme);
    });
  }

  function updateThemeIcon(theme) {
    if (!themeToggleBtn) return;
    if (theme === 'dark') {
      // Show Sun icon for switching to light
      themeToggleBtn.innerHTML = `
        <svg viewBox="0 0 24 24" width="20" height="20">
          <path fill="currentColor" d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58c-.39-.39-1.03-.39-1.41 0s-.39 1.03 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41L5.99 4.58zm12.37 12.37c-.39-.39-1.03-.39-1.41 0s-.39 1.03 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41l-1.06-1.06zm1.06-10.96c.39-.39.39-1.03 0-1.41s-1.03-.39-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06zM7.05 18.36l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06c.39-.39.39-1.03 0-1.41s-1.03-.39-1.41 0z"/>
        </svg>
      `;
      themeToggleBtn.setAttribute('title', 'Switch to Light Mode');
    } else {
      // Show Moon icon for switching to dark
      themeToggleBtn.innerHTML = `
        <svg viewBox="0 0 24 24" width="20" height="20">
          <path fill="currentColor" d="M12 3c-4.97 0-9 4.03-9 9 0 2.12.74 4.07 1.97 5.61L4.35 19.4c-.39.39-.39 1.02 0 1.41.39.39 1.02.39 1.41 0l1.9-1.9C9.28 19.67 10.59 20 12 20c4.97 0 9-4.03 9-9 0-.46-.04-.92-.1-1.36-.98 1.37-2.58 2.26-4.4 2.26-3.03 0-5.5-2.47-5.5-5.5 0-1.82.89-3.42 2.26-4.4-.44-.06-.9-.1-1.36-.1z"/>
        </svg>
      `;
      themeToggleBtn.setAttribute('title', 'Switch to Dark Mode');
    }
  }

  // 2. Mobile Navigation Drawer Toggle
  const mobileToggleBtn = document.getElementById('mobile-toggle');
  const navBar = document.querySelector('.header-nav-bar');
  const navMenu = document.getElementById('nav-menu');

  function setMobileNavOpen(open) {
    if (navBar) {
      navBar.classList.toggle('open', open);
      navBar.classList.toggle('mobile-open', open);
    }
    if (navMenu) {
      navMenu.classList.toggle('open', open);
      navMenu.classList.toggle('mobile-open', open);
    }
    if (mobileToggleBtn) {
      mobileToggleBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      mobileToggleBtn.innerHTML = open ? '✕' : '☰';
    }
  }

  if (mobileToggleBtn && (navBar || navMenu)) {
    mobileToggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isCurrentlyOpen = navBar ? navBar.classList.contains('open') : (navMenu && navMenu.classList.contains('open'));
      setMobileNavOpen(!isCurrentlyOpen);
    });
  }

  // Close mobile nav when clicking any nav link
  document.querySelectorAll('.header-nav-bar .nav-link, .header-nav-bar .dropdown-item').forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth <= 850) {
        setMobileNavOpen(false);
      }
    });
  });

  // Close mobile nav on click outside
  document.addEventListener('click', (e) => {
    const isInsideNav = (navBar && navBar.contains(e.target)) || (navMenu && navMenu.contains(e.target));
    const isToggle = mobileToggleBtn && mobileToggleBtn.contains(e.target);
    if (!isInsideNav && !isToggle) {
      setMobileNavOpen(false);
    }
  });

  // 3. Highlight Active Navigation Item
  const currentPath = window.location.pathname.replace(/\/index\.html$/, '/').replace(/\/$/, '') || '/';
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    const linkPath = link.getAttribute('href').replace(/\/index\.html$/, '/').replace(/\/$/, '') || '/';
    if (linkPath === currentPath || (linkPath !== '/' && currentPath.startsWith(linkPath))) {
      link.classList.add('active');
    }
  });
});

/**
 * Global Toast Notification Helper
 */
function showToast(message) {
  let toast = document.getElementById('global-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'global-toast';
    toast.className = 'toast-notice';
    document.body.appendChild(toast);
  }
  toast.innerHTML = `
    <svg viewBox="0 0 24 24" width="18" height="18" fill="#10b981">
      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
    </svg>
    <span>${message}</span>
  `;
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 2500);
}
