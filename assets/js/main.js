/**
 * Conscious Brain Lab - Main JavaScript
 * Handles Dark/Light Mode, Mobile Navigation, and Global UI Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Theme Management (Dark / Light Mode)
  const themeToggleBtn = document.getElementById('theme-toggle');
  const darkQuery = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  const lightQuery = window.matchMedia ? window.matchMedia('(prefers-color-scheme: light)') : null;
  const savedTheme = localStorage.getItem('cbl-theme');

  if (themeToggleBtn && !themeToggleBtn.querySelector('.theme-toggle-thumb')) {
    themeToggleBtn.innerHTML = `
      <span class="theme-toggle-thumb" aria-hidden="true"></span>
      <span class="theme-toggle-slot theme-toggle-slot--sun" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="15" height="15"><circle cx="12" cy="12" r="4" fill="currentColor"/><g stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><line x1="12" y1="2.5" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="21.5"/><line x1="2.5" y1="12" x2="5" y2="12"/><line x1="19" y1="12" x2="21.5" y2="12"/><line x1="5.28" y1="5.28" x2="7.05" y2="7.05"/><line x1="16.95" y1="16.95" x2="18.72" y2="18.72"/><line x1="18.72" y1="5.28" x2="16.95" y2="7.05"/><line x1="7.05" y1="16.95" x2="5.28" y2="18.72"/></g></svg>
      </span>
      <span class="theme-toggle-slot theme-toggle-slot--moon" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="14" height="14"><path fill="currentColor" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
      </span>
    `;
  }

  function getMachineTheme() {
    if (darkQuery && darkQuery.matches) return 'dark';
    if (lightQuery && lightQuery.matches) return 'light';
    return null;
  }

  function getTimezoneCoordinates(date) {
    const tz = Intl.DateTimeFormat ? Intl.DateTimeFormat().resolvedOptions().timeZone : '';
    const coordsByTz = {
      'Europe/Amsterdam': [52.37, 4.90],
      'Europe/Brussels': [50.85, 4.35],
      'Europe/London': [51.51, -0.13],
      'Europe/Paris': [48.86, 2.35],
      'Europe/Berlin': [52.52, 13.40],
      'Europe/Zurich': [47.37, 8.54],
      'Europe/Madrid': [40.42, -3.70],
      'Europe/Rome': [41.90, 12.50],
      'Europe/Stockholm': [59.33, 18.07],
      'Europe/Oslo': [59.91, 10.75],
      'Europe/Copenhagen': [55.68, 12.57],
      'Europe/Warsaw': [52.23, 21.01],
      'Europe/Athens': [37.98, 23.73],
      'Europe/Istanbul': [41.01, 28.98],
      'Europe/Moscow': [55.76, 37.62],
      'America/New_York': [40.71, -74.01],
      'America/Toronto': [43.65, -79.38],
      'America/Chicago': [41.88, -87.63],
      'America/Denver': [39.74, -104.99],
      'America/Los_Angeles': [34.05, -118.24],
      'America/Vancouver': [49.28, -123.12],
      'America/Mexico_City': [19.43, -99.13],
      'America/Sao_Paulo': [-23.55, -46.63],
      'America/Argentina/Buenos_Aires': [-34.60, -58.38],
      'Asia/Tokyo': [35.68, 139.77],
      'Asia/Seoul': [37.57, 126.98],
      'Asia/Shanghai': [31.23, 121.47],
      'Asia/Hong_Kong': [22.32, 114.17],
      'Asia/Singapore': [1.35, 103.82],
      'Asia/Kolkata': [28.61, 77.21],
      'Asia/Dubai': [25.20, 55.27],
      'Australia/Sydney': [-33.87, 151.21],
      'Australia/Melbourne': [-37.81, 144.96],
      'Pacific/Auckland': [-36.85, 174.76],
      'Africa/Cairo': [30.04, 31.24],
      'Africa/Johannesburg': [-26.20, 28.05]
    };
    if (tz && coordsByTz[tz]) return coordsByTz[tz];

    // Estimate coordinates from timezone offset and region if not in lookup table
    const approxLon = (-date.getTimezoneOffset() / 60) * 15;
    const region = tz.split('/')[0];
    const regionLat = { Europe: 50, America: 38, Asia: 34, Australia: -33, Pacific: -30, Africa: 5 };
    return [regionLat[region] ?? 40, approxLon];
  }

  function getTimeOfDayTheme(now = new Date()) {
    // Calculate solar sunrise/sunset for the current timezone & date (NOAA equation)
    const [lat, lon] = getTimezoneCoordinates(now);
    const dayOfYear = Math.floor(
      (Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()) - Date.UTC(now.getFullYear(), 0, 0)) / 86400000
    );
    const gamma = ((2 * Math.PI) / 365) * (dayOfYear - 1);
    const eqtime = 229.18 * (
      0.000075 +
      0.001868 * Math.cos(gamma) -
      0.032077 * Math.sin(gamma) -
      0.014615 * Math.cos(2 * gamma) -
      0.040849 * Math.sin(2 * gamma)
    );
    const decl =
      0.006918 -
      0.399912 * Math.cos(gamma) +
      0.070257 * Math.sin(gamma) -
      0.006758 * Math.cos(2 * gamma) +
      0.000907 * Math.sin(2 * gamma) -
      0.002697 * Math.cos(3 * gamma) +
      0.00148 * Math.sin(3 * gamma);

    const latRad = (lat * Math.PI) / 180;
    const zenithRad = (90.833 * Math.PI) / 180;
    const cosHA = Math.cos(zenithRad) / (Math.cos(latRad) * Math.cos(decl)) - Math.tan(latRad) * Math.tan(decl);

    if (cosHA > 1) return 'dark';  // Polar night
    if (cosHA < -1) return 'light'; // Midnight sun

    const haDeg = (Math.acos(cosHA) * 180) / Math.PI;
    const tzOffsetMin = -now.getTimezoneOffset();
    const sunriseLocal = (((720 - 4 * (lon + haDeg) - eqtime + tzOffsetMin) % 1440) + 1440) % 1440;
    const sunsetLocal = (((720 - 4 * (lon - haDeg) - eqtime + tzOffsetMin) % 1440) + 1440) % 1440;
    const nowLocal = now.getHours() * 60 + now.getMinutes() + now.getSeconds() / 60;

    const isDaylight = sunriseLocal < sunsetLocal
      ? nowLocal >= sunriseLocal && nowLocal < sunsetLocal
      : nowLocal >= sunriseLocal || nowLocal < sunsetLocal;

    return isDaylight ? 'light' : 'dark';
  }

  function resolveAutomaticTheme() {
    return getMachineTheme() || getTimeOfDayTheme();
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    updateThemeIcon(theme);
  }

  const currentTheme = savedTheme || resolveAutomaticTheme();
  applyTheme(currentTheme);

  const handleMachineThemeChange = () => {
    if (!localStorage.getItem('cbl-theme')) {
      applyTheme(resolveAutomaticTheme());
    }
  };

  if (darkQuery && darkQuery.addEventListener) {
    darkQuery.addEventListener('change', handleMachineThemeChange);
  }
  if (lightQuery && lightQuery.addEventListener) {
    lightQuery.addEventListener('change', handleMachineThemeChange);
  }

  if (themeToggleBtn) {
    themeToggleBtn.setAttribute('role', 'switch');
    themeToggleBtn.addEventListener('click', () => {
      const activeTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
      applyTheme(newTheme);
      localStorage.setItem('cbl-theme', newTheme);
    });
  }

  function updateThemeIcon(theme) {
    if (!themeToggleBtn) return;
    const isDark = theme === 'dark';
    themeToggleBtn.setAttribute('aria-checked', isDark ? 'true' : 'false');
    themeToggleBtn.setAttribute('title', isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode');
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
