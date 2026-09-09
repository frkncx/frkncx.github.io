    // ── Video preview on hover ────────────────────────────────────────────────
    // Touch devices have no hover, so they play whatever is centred on screen.
    (function () {
        const wraps = document.querySelectorAll('[data-preview]');

        function showVideo(wrap) {
            const thumb = wrap.querySelector('.preview-thumb');
            const video = wrap.querySelector('.preview-video');
            if (!thumb || !video) return;
            thumb.style.display = 'none';
            video.style.display = 'block';
            video.currentTime = 0;
            // Leave the frame up if autoplay is refused; snapping back reads as broken.
            const played = video.play();
            if (played) played.catch(() => { });
        }

        function showThumb(wrap) {
            const thumb = wrap.querySelector('.preview-thumb');
            const video = wrap.querySelector('.preview-video');
            if (!thumb || !video) return;
            video.pause();
            video.style.display = 'none';
            thumb.style.display = 'block';
        }

        if (window.matchMedia('(hover: hover)').matches) {
            wraps.forEach(wrap => {
                wrap.addEventListener('mouseenter', () => showVideo(wrap));
                wrap.addEventListener('mouseleave', () => showThumb(wrap));
            });
            return;
        }

        // Touch: play after a short dwell once the card is on screen.
        const DWELL_MS = 1200;
        const timers = new WeakMap();

        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                const wrap = entry.target;
                clearTimeout(timers.get(wrap));
                if (entry.isIntersecting) {
                    timers.set(wrap, setTimeout(() => showVideo(wrap), DWELL_MS));
                } else {
                    showThumb(wrap);
                }
            });
        }, { threshold: 0.5 });

        wraps.forEach(wrap => observer.observe(wrap));
    })();

    // ── Mobile nav toggle ─────────────────────────────────────────────────────
    (function () {
        const toggle = document.getElementById('navToggle');
        const nav = document.getElementById('mainNav');
        if (!toggle || !nav) return;

        toggle.addEventListener('click', () => {
            nav.classList.toggle('nav-open');
        });

        // Close menu after tapping a link
        nav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                nav.classList.remove('nav-open');
            });
        });
    })();

    if (window.matchMedia('(hover: none)').matches) {
  document.querySelectorAll('.hover-container').forEach(container => {
    container.addEventListener('click', (e) => {
      if (!container.classList.contains('tapped')) {
        e.preventDefault();
        e.stopPropagation();
        document.querySelectorAll('.hover-container.tapped')
                .forEach(c => c !== container && c.classList.remove('tapped'));
        container.classList.add('tapped');
      }
      // already open: click falls through and the link navigates
    });
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.hover-container')) {
      document.querySelectorAll('.hover-container.tapped')
              .forEach(c => c.classList.remove('tapped'));
    }
  });
}

// ── Collapsible project sections (mobile only) ────────────────────────────
// Fifteen cards in one column is an endless scroll on a phone.
(function () {
    const mq = window.matchMedia('(max-width: 768px)');
    const sections = [...document.querySelectorAll('.project-subsection')];
    if (!sections.length) return;

    function build() {
        sections.forEach((sec, i) => {
            const heading = sec.querySelector('h3');
            const carousel = sec.querySelector('.carousel');
            if (!heading || !carousel) return;

            if (!mq.matches) {
                heading.removeAttribute('role');
                heading.removeAttribute('tabindex');
                heading.classList.remove('is-toggle');
                sec.classList.remove('is-collapsed');
                return;
            }

            heading.setAttribute('role', 'button');
            heading.setAttribute('tabindex', '0');
            heading.classList.add('is-toggle');
            if (!heading.dataset.bound) {
                const toggle = () => {
                    sec.classList.toggle('is-collapsed');
                    heading.setAttribute('aria-expanded', String(!sec.classList.contains('is-collapsed')));
                };
                heading.addEventListener('click', toggle);
                heading.addEventListener('keydown', e => {
                    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
                });
                heading.dataset.bound = '1';
            }
            // Flagship stays open; the rest start closed.
            const collapsed = i > 0;
            sec.classList.toggle('is-collapsed', collapsed);
            heading.setAttribute('aria-expanded', String(!collapsed));
        });
    }

    build();
    mq.addEventListener('change', build);
})();

// ── Collapse card descriptions longer than the shortest full one ──────────
(function () {
    const LIMIT = 142;   // Memento Mori's description is the baseline that stays open

    document.querySelectorAll('.carousel .item > p').forEach(desc => {
        if (desc.classList.contains('project-meta')) return;
        if (desc.textContent.trim().length <= LIMIT) return;

        desc.classList.add('desc-clamped');

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'tech-link desc-toggle';
        btn.textContent = 'Read more';
        btn.setAttribute('aria-expanded', 'false');

        btn.addEventListener('click', () => {
            const open = desc.classList.toggle('desc-clamped') === false;
            btn.textContent = open ? 'Show less' : 'Read more';
            btn.setAttribute('aria-expanded', String(open));
        });

        desc.after(btn);
    });
})();

// ── Devlogs index: 16 per page, numbered pager ────────────────────────────
(function () {
    const PER_PAGE = 16;   // 4 x 4
    const grid = document.getElementById('devlogGrid');
    const pager = document.getElementById('devlogPager');
    if (!grid || !pager) return;

    const cards = [...grid.querySelectorAll('.devlog-card')];
    let page = 1;

    function visible() {
        return cards;   // filtering hooks in here later
    }

    function render() {
        const items = visible();
        const pages = Math.max(1, Math.ceil(items.length / PER_PAGE));
        page = Math.min(page, pages);

        cards.forEach(c => c.classList.add('is-hidden'));
        items.slice((page - 1) * PER_PAGE, page * PER_PAGE)
            .forEach(c => c.classList.remove('is-hidden'));

        pager.hidden = pages < 2;
        if (pager.hidden) return;

        pager.replaceChildren();
        const add = (label, target, opts = {}) => {
            const b = document.createElement('button');
            b.type = 'button';
            b.textContent = label;
            if (opts.current) b.setAttribute('aria-current', 'true');
            if (opts.disabled) b.disabled = true;
            else b.addEventListener('click', () => { page = target; render(); grid.scrollIntoView({ block: 'start' }); });
            pager.append(b);
        };

        add('Prev', page - 1, { disabled: page === 1 });
        for (let i = 1; i <= pages; i++) add(String(i), i, { current: i === page });
        add('Next', page + 1, { disabled: page === pages });
    }

    render();
})();
