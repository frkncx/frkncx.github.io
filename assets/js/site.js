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
            const played = video.play();
            if (played) played.catch(() => showThumb(wrap));
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

        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting && entry.intersectionRatio > 0.75) {
                    showVideo(entry.target);
                } else {
                    showThumb(entry.target);
                }
            });
        }, { threshold: [0, 0.75] });

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
