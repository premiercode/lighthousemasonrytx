/* =====================================================================
   Lighthouse Masonry, Inc. — progressive enhancement
   The page is fully usable without this file (the hero build is pure
   CSS). Each module is self-contained and guarded so it also runs on
   404.html, which has the header and footer but no homepage sections.
   ===================================================================== */
(() => {
  'use strict';

  const root = document.documentElement;
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const desktopNav = window.matchMedia('(min-width: 1024px)'); // keep in sync with styles.css
  const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

  const isVisible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
    && getComputedStyle(el).visibility !== 'hidden';

  /* --- Header: solid background once the page scrolls ------------- */
  function initHeader() {
    const header = document.querySelector('[data-header]');
    if (!header) return;
    const update = () => header.classList.toggle('is-scrolled', window.scrollY > 24);
    update();
    window.addEventListener('scroll', update, { passive: true });
  }

  /* --- Mobile nav ---------------------------------------------------
     Upgrades the footer-anchor link into a disclosure button.
     While open: main + footer are inert, focus moves into the menu,
     and Tab cycles through every visible focusable in the header
     (brand, menu items, phone, CTA, toggle) in DOM order.            */
  const mobileNav = { isOpen: () => false, close: () => {} };

  function initMobileNav() {
    const header = document.querySelector('[data-header]');
    const toggle = document.querySelector('[data-menu-toggle]');
    const nav = document.querySelector('[data-nav]');
    if (!header || !toggle || !nav) return;

    // Everything outside the header goes inert while the menu is open (the skip link too)
    const outside = [document.querySelector('.skip-link'), document.querySelector('main'), document.querySelector('footer'), document.querySelector('.demo-note')].filter(Boolean);

    toggle.setAttribute('role', 'button');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.removeAttribute('href');
    toggle.tabIndex = 0;

    const focusables = (scope) => [...scope.querySelectorAll(FOCUSABLE)].filter(isVisible);

    const setOpen = (open, { returnFocus = false } = {}) => {
      root.classList.toggle('nav-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      outside.forEach((el) => { el.inert = open; });
      if (open) {
        // The panel becomes visible after a style pass; retry briefly until focus lands
        let tries = 0;
        const focusFirst = () => {
          const first = nav.querySelector('.primary-nav__link') || focusables(nav)[0];
          first?.focus();
          if (document.activeElement !== first && mobileNav.isOpen() && ++tries < 10) setTimeout(focusFirst, 40);
        };
        setTimeout(focusFirst, 30);
      } else if (returnFocus) {
        toggle.focus();
      }
    };

    mobileNav.isOpen = () => root.classList.contains('nav-open');
    mobileNav.close = () => setOpen(false);

    toggle.addEventListener('click', () => setOpen(!mobileNav.isOpen()));
    toggle.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle.click(); }
    });

    document.addEventListener('keydown', (e) => {
      if (!mobileNav.isOpen()) return;

      if (e.key === 'Escape') { setOpen(false, { returnFocus: true }); return; }

      if (e.key === 'Tab') {
        const cycle = focusables(header);
        if (!cycle.length) return;
        const first = cycle[0];
        const last = cycle[cycle.length - 1];
        const i = cycle.indexOf(document.activeElement);
        if (i === -1) { e.preventDefault(); (e.shiftKey ? last : first).focus(); }
        else if (e.shiftKey && i === 0) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && i === cycle.length - 1) { e.preventDefault(); first.focus(); }
      }
    });

    nav.addEventListener('click', (e) => {
      if (e.target.closest('a')) setOpen(false);
    });

    desktopNav.addEventListener('change', (e) => { if (e.matches) setOpen(false); });
  }

  /* --- Submenus -----------------------------------------------------
     Button toggles .is-open (keyboard path). Hover opens via CSS on
     desktop, and aria-expanded follows it. Escape dismisses either
     until the pointer/focus leaves.                                  */
  function initSubmenus() {
    document.querySelectorAll('[data-submenu]').forEach((item) => {
      const btn = item.querySelector('.sub-toggle');
      if (!btn) return;

      const sync = () => {
        const hoverOpen = desktopNav.matches && item.matches(':hover') && !item.classList.contains('is-dismissed');
        btn.setAttribute('aria-expanded', String(item.classList.contains('is-open') || hoverOpen));
      };

      const close = () => {
        item.classList.remove('is-open');
        sync();
      };

      btn.addEventListener('click', () => {
        const open = !item.classList.contains('is-open');
        item.classList.toggle('is-open', open);
        item.classList.remove('is-dismissed');
        sync();
      });

      item.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        // A tapped item keeps :hover on touch screens, so hover only counts on desktop
        // and only once; otherwise Escape could never reach the mobile menu.
        const hoverOpen = desktopNav.matches && item.matches(':hover') && !item.classList.contains('is-dismissed');
        const wasOpen = item.classList.contains('is-open') || hoverOpen;
        if (!wasOpen) return;
        e.stopPropagation();
        item.classList.add('is-dismissed');
        close();
        btn.focus();
      });

      item.addEventListener('focusout', (e) => {
        if (!item.contains(e.relatedTarget)) {
          item.classList.remove('is-dismissed');
          close();
        }
      });

      item.addEventListener('mouseenter', sync);
      item.addEventListener('mouseleave', () => {
        item.classList.remove('is-dismissed');
        // :hover clears after this event fires
        requestAnimationFrame(sync);
      });

      document.addEventListener('click', (e) => { if (!item.contains(e.target)) close(); });
    });

    // Escape also dismisses a purely hover-opened menu when focus is elsewhere
    document.addEventListener('keydown', (e) => {
      if (e.key !== 'Escape') return;
      document.querySelectorAll('[data-submenu]:hover').forEach((item) => {
        item.classList.add('is-dismissed');
        item.querySelector('.sub-toggle')?.setAttribute('aria-expanded', String(item.classList.contains('is-open')));
      });
    });
  }

  /* --- Hero wall: only build what's on screen -----------------------
     The wall SVG is 2400 units wide and sliced to the viewport, so on a
     phone most of it is off screen. Bricks outside the visible slice are
     tagged and skip the build animation (see .is-offscreen in CSS).     */
  function initHeroWall() {
    const wall = document.querySelector('[data-hero-wall]');
    const svg = wall?.querySelector('svg');
    if (!svg || wall.closest('.hero--built') || prefersReducedMotion) return;

    const [, , vbW, vbH] = svg.getAttribute('viewBox').split(/\s+/).map(Number);
    const { width, height } = svg.getBoundingClientRect();
    if (!width || !height) return;
    const scale = Math.max(width / vbW, height / vbH);   // "slice"
    const visible = width / scale;
    const x0 = (vbW - visible) / 2;                        // "xMid"
    const x1 = x0 + visible;
    if (x0 <= 0) return;

    svg.querySelectorAll('.b, .sh, .cap, .cope').forEach((el) => {
      const box = el.getBBox();
      if (box.x + box.width < x0 - 4 || box.x > x1 + 4) el.classList.add('is-offscreen');
    });
  }

  /* --- Before / after slider ----------------------------------------
     The native range input is the control (keyboard, touch, screen
     readers for free). JS mirrors its value into --pos, keeps
     aria-valuetext readable, and lets a single tap or click jump the
     split to that point (no drag needed, WCAG 2.5.7). Without JS the
     split rests at 50%.*/
  function initBeforeAfter() {
    document.querySelectorAll('[data-ba]').forEach((ba) => {
      const range = ba.querySelector('input[type="range"]');
      if (!range) return;

      let frame = 0;
      const apply = () => {
        frame = 0;
        const v = Number(range.value);
        ba.style.setProperty('--pos', `${v}%`);
        range.setAttribute('aria-valuetext', `${v}% before, ${100 - v}% after`);
      };
      const schedule = () => { if (!frame) frame = requestAnimationFrame(apply); };

      range.addEventListener('input', schedule);

      // Pointer input is handled on the wrapper; the range stays the keyboard
      // and screen-reader control (it has pointer-events: none in CSS).
      // A tap (moved < 10px) jumps the split, a mostly-horizontal drag moves
      // it, and a vertical swipe is left to scroll the page (touch-action: pan-y).
      const setFromX = (clientX) => {
        const r = ba.getBoundingClientRect();
        if (!r.width) return;
        const min = Number(range.min) || 0;
        const max = Number(range.max) || 100;
        const v = Math.round(min + ((clientX - r.left) / r.width) * (max - min));
        range.value = String(Math.min(max, Math.max(min, v)));
        schedule();
      };
      let start = null;
      let dragging = false;
      ba.addEventListener('pointerdown', (e) => {
        if (e.button !== 0) return;
        start = { x: e.clientX, y: e.clientY, id: e.pointerId };
        dragging = false;
      });
      ba.addEventListener('pointermove', (e) => {
        if (!start || e.pointerId !== start.id) return;
        const dx = e.clientX - start.x;
        const dy = e.clientY - start.y;
        if (!dragging && Math.abs(dx) >= 10 && Math.abs(dx) > Math.abs(dy)) {
          dragging = true;
          ba.setPointerCapture?.(e.pointerId);
        }
        if (dragging) { e.preventDefault(); setFromX(e.clientX); }
      });
      ba.addEventListener('pointerup', (e) => {
        if (!start || e.pointerId !== start.id) return;
        const moved = Math.hypot(e.clientX - start.x, e.clientY - start.y);
        if (!dragging && moved < 10) setFromX(e.clientX);
        start = null;
        dragging = false;
      });
      ba.addEventListener('pointercancel', () => { start = null; dragging = false; });

      // Fallback for browsers without :has() — mirror focus-visible onto the wrapper
      range.addEventListener('focus', () => ba.classList.toggle('is-focused', range.matches(':focus-visible')));
      range.addEventListener('blur', () => ba.classList.remove('is-focused'));
      apply();
    });
  }

  /* --- Estimate form -------------------------------------------------
     Every link to #estimate goes through one handler: close the mobile
     menu, pre-fill from data-estimate (service or project type) when
     present, scroll to the form and focus the Name field. Submission is
     intercepted: this is a static demo.                               */
  function initEstimate() {
    const form = document.querySelector('[data-estimate-form]');
    if (!form) return;

    const service = form.querySelector('#f-service');
    const status = form.querySelector('[data-estimate-status]');
    const nameField = form.querySelector('#f-name');

    const goToForm = ({ smooth = true } = {}) => {
      form.scrollIntoView({ behavior: smooth && !prefersReducedMotion ? 'smooth' : 'auto', block: 'start' });
      nameField?.focus({ preventScroll: true });
    };

    document.querySelectorAll('a[href="#estimate"], a[href="/#estimate"], [data-estimate]').forEach((link) => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        if (mobileNav.isOpen()) mobileNav.close(); // un-inert main before focusing into it
        const value = link.dataset.estimate;
        if (value) {
          const type = form.querySelector(`input[name="project_type"][value="${value}"]`);
          const option = service && [...service.options].find((o) => o.value === value);
          if (type) type.checked = true;
          if (option) service.value = value;
        }
        if (location.hash !== '#estimate') history.pushState(null, '', '#estimate');
        goToForm();
      });
    });

    // Arriving from another page (e.g. the 404's "Get a free estimate"). The
    // browser's own fragment handling can run after DOMContentLoaded, so
    // focus again once the page has fully loaded.
    if (location.hash === '#estimate') {
      goToForm({ smooth: false });
      if (document.readyState !== 'complete') {
        window.addEventListener('load', () => { if (document.activeElement !== nameField) goToForm({ smooth: false }); }, { once: true });
      }
    }

    form.addEventListener('submit', (e) => {
      // Mockup only. Production: bail if the honeypot is filled, fetch a
      // reCAPTCHA v3 token, then POST to the backend.
      e.preventDefault();
      if (form.querySelector('#f-website')?.value) return;
      if (!status) return;
      const name = nameField?.value.trim().split(/\s+/)[0] || 'there';
      // Clear, then set after a beat so screen readers announce repeat submits
      status.textContent = '';
      setTimeout(() => {
        status.textContent = `Thanks, ${name}. This is a design preview, so nothing was sent. On the live site this request goes straight to the office.`;
      }, 100);
    });
  }

  /* --- Reveal-on-scroll ---------------------------------------------- */
  function initReveal() {
    const items = document.querySelectorAll('[data-reveal]');

    if (prefersReducedMotion || !('IntersectionObserver' in window)) {
      items.forEach((el) => el.classList.add('is-visible'));
      return;
    }

    // Stagger siblings that share a parent (cards in a grid, etc.)
    const groups = new Map();
    items.forEach((el) => {
      const p = el.parentElement;
      const i = groups.get(p) || 0;
      el.style.setProperty('--reveal-delay', `${Math.min(i, 6) * 70}ms`);
      groups.set(p, i + 1);
    });

    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0 });

    items.forEach((el) => io.observe(el));
  }

  /* --- 404: show the path that was asked for ------------------------ */
  function initNotFound() {
    const el = document.querySelector('[data-nf-path]');
    const code = el?.querySelector('code');
    if (!code || location.pathname === '/404.html') return;
    let path = location.pathname;
    try { path = decodeURI(path); } catch { /* keep the raw path */ }
    code.textContent = path;
    el.hidden = false;
  }

  /* --- Footer year ------------------------------------------------- */
  function initYear() {
    document.querySelectorAll('[data-year]').forEach((el) => { el.textContent = new Date().getFullYear(); });
  }

  const init = () => {
    initHeader();
    initMobileNav();
    initSubmenus();
    initHeroWall();
    initBeforeAfter();
    initEstimate();
    initReveal();
    initNotFound();
    initYear();
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
