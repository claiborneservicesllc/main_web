// Claiborne Services LLC — shared interactivity
(function () {
  'use strict';

  // Mobile nav toggle
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.main-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // FAQ accordion (accessible)
  document.querySelectorAll('.faq-q').forEach(function (btn) {
    btn.setAttribute('aria-expanded', 'false');
    btn.addEventListener('click', function () {
      var item = btn.closest('.faq-item');
      var isOpen = item.classList.toggle('open');
      btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
  });

  // Before/after sliders
  document.querySelectorAll('.ba-slider').forEach(function (slider) {
    var after = slider.querySelector('.ba-after');
    var handle = slider.querySelector('.ba-handle');
    if (!after || !handle) return;
    var dragging = false;
    function setPos(clientX) {
      var rect = slider.getBoundingClientRect();
      var pct = ((clientX - rect.left) / rect.width) * 100;
      pct = Math.max(0, Math.min(100, pct));
      after.style.clipPath = 'inset(0 0 0 ' + pct + '%)';
      handle.style.left = pct + '%';
    }
    function start(e) { dragging = true; move(e); }
    function move(e) {
      if (!dragging) return;
      var x = e.touches ? e.touches[0].clientX : e.clientX;
      setPos(x);
      if (e.cancelable) e.preventDefault();
    }
    function end() { dragging = false; }
    handle.addEventListener('mousedown', start);
    slider.addEventListener('mousedown', start);
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', end);
    handle.addEventListener('touchstart', start, { passive: true });
    slider.addEventListener('touchstart', start, { passive: true });
    window.addEventListener('touchmove', move, { passive: false });
    window.addEventListener('touchend', end);
    // keyboard
    handle.setAttribute('tabindex', '0');
    handle.setAttribute('role', 'slider');
    handle.setAttribute('aria-label', 'Drag to compare before and after');
    var pos = 50;
    handle.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') pos = Math.max(0, pos - 4);
      else if (e.key === 'ArrowRight') pos = Math.min(100, pos + 4);
      else return;
      after.style.clipPath = 'inset(0 0 0 ' + pos + '%)';
      handle.style.left = pos + '%';
      e.preventDefault();
    });
  });

  // Gallery filter
  var chips = document.querySelectorAll('.chip');
  var items = document.querySelectorAll('[data-cat]');
  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      chips.forEach(function (c) { c.classList.remove('active'); });
      chip.classList.add('active');
      var filter = chip.getAttribute('data-filter');
      items.forEach(function (item) {
        var show = filter === 'all' || item.getAttribute('data-cat') === filter;
        item.style.display = show ? '' : 'none';
      });
    });
  });

  // Lightbox
  var lb = document.querySelector('.lightbox');
  if (lb) {
    var lbImg = lb.querySelector('img');
    var lbClose = lb.querySelector('.lightbox-close');
    document.querySelectorAll('[data-lightbox]').forEach(function (img) {
      img.addEventListener('click', function () {
        lbImg.src = img.getAttribute('data-full') || img.src;
        lbImg.alt = img.alt;
        lb.classList.add('open');
      });
    });
    function close() { lb.classList.remove('open'); }
    lbClose.addEventListener('click', close);
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  }

  // Contact form handler — POSTs to Formspree
  var form = document.querySelector('.quote-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var successNote = form.querySelector('.form-success');
      var errorNote = form.querySelector('.form-error');
      var submitBtn = form.querySelector('button[type="submit"]');
      var originalBtnText = submitBtn ? submitBtn.textContent : '';
      if (successNote) successNote.style.display = 'none';
      if (errorNote) errorNote.style.display = 'none';
      if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Sending…'; }

      var data = new FormData(form);
      fetch(form.action, {
        method: 'POST',
        body: data,
        headers: { 'Accept': 'application/json' }
      }).then(function (response) {
        if (response.ok) {
          if (successNote) successNote.style.display = 'block';
          form.reset();
        } else {
          response.json().then(function (data) {
            if (errorNote) errorNote.style.display = 'block';
          }).catch(function () {
            if (errorNote) errorNote.style.display = 'block';
          });
        }
      }).catch(function () {
        if (errorNote) errorNote.style.display = 'block';
      }).finally(function () {
        if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = originalBtnText; }
      });
    });
  }
})();

  // ============================================================
  // Conversion tracking — fires gtag events on key CTAs
  // ============================================================
  (function () {
    function track(name, params) {
      if (typeof window.gtag === 'function') {
        try { window.gtag('event', name, params || {}); } catch (e) {}
      }
    }
    // Phone clicks
    document.querySelectorAll('a[href^="tel:"]').forEach(function (a) {
      a.addEventListener('click', function () {
        track('call_click', { phone: a.getAttribute('href'), source: location.pathname });
      });
    });
    // SMS clicks
    document.querySelectorAll('a[href^="sms:"]').forEach(function (a) {
      a.addEventListener('click', function () {
        track('sms_click', { phone: a.getAttribute('href'), source: location.pathname });
      });
    });
    // Email clicks
    document.querySelectorAll('a[href^="mailto:"]').forEach(function (a) {
      a.addEventListener('click', function () {
        track('email_click', { source: location.pathname });
      });
    });
    // Get a Quote CTA clicks
    document.querySelectorAll('a[href*="contact.html"]').forEach(function (a) {
      a.addEventListener('click', function () {
        track('quote_cta_click', { label: (a.textContent || '').trim().slice(0, 40), source: location.pathname });
      });
    });
    // Quote form submit
    var qf = document.querySelector('.quote-form');
    if (qf) {
      qf.addEventListener('submit', function () {
        track('quote_form_submit', { source: location.pathname });
      });
    }
  })();

  // ============================================================
  // Open/Closed badge — driven from data-hours on the badge element
  // Format: data-hours="Mo 07:00-18:00;Tu 07:00-18:00;...;Sa 08:00-12:00"
  // ============================================================
  (function () {
    var el = document.querySelector('[data-open-status]');
    if (!el) return;
    var hours = (el.getAttribute('data-hours') || '').split(';').reduce(function (acc, part) {
      var m = part.trim().match(/^(Mo|Tu|We|Th|Fr|Sa|Su)\s+(\d{2}):(\d{2})-(\d{2}):(\d{2})$/);
      if (m) acc[m[1]] = { open: (+m[2]) * 60 + (+m[3]), close: (+m[4]) * 60 + (+m[5]) };
      return acc;
    }, {});
    var dayMap = ['Su','Mo','Tu','We','Th','Fr','Sa'];
    function update() {
      // Use Central Time (America/Chicago) — Shawn's tz
      var nowCT = new Date(new Date().toLocaleString('en-US', { timeZone: 'America/Chicago' }));
      var day = dayMap[nowCT.getDay()];
      var mins = nowCT.getHours() * 60 + nowCT.getMinutes();
      var h = hours[day];
      var isOpen = !!(h && mins >= h.open && mins < h.close);
      el.classList.toggle('is-open', isOpen);
      el.classList.toggle('is-closed', !isOpen);
      var dot = el.querySelector('.status-dot');
      var txt = el.querySelector('.status-text');
      if (dot) dot.setAttribute('aria-hidden', 'true');
      if (txt) {
        if (isOpen) {
          txt.textContent = 'Open now · answering calls';
        } else {
          // Find next opening time
          var label = 'Closed · leave a message';
          for (var i = 1; i <= 7; i++) {
            var nd = dayMap[(nowCT.getDay() + i) % 7];
            if (hours[nd]) { label = 'Closed · opens ' + nd + ' ' + String(Math.floor(hours[nd].open / 60)).padStart(2,'0') + ':' + String(hours[nd].open % 60).padStart(2,'0'); break; }
          }
          txt.textContent = label;
        }
      }
    }
    update();
    setInterval(update, 60000);
  })();
