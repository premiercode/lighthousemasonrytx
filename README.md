# Lighthouse Masonry, Inc.: homepage design mockup

Design preview prepared by Premier Code Inc. for Lighthouse Masonry, Inc. (Dallas–Fort Worth, TX).

- Preview: https://lighthousemasonrytx.premiercodeinc.com/
- Static HTML/CSS/JS with no build step, hosted on GitHub Pages. Serve the folder from its root (links are root-relative, e.g. `/services/archways/`), or open `index.html` directly for a quick look (root-relative links won't resolve over `file://`).
- Content and figures marked `<!-- PLACEHOLDER -->` still need client confirmation. The phone number, email, address, stats, testimonials, rating, project specs and service-area towns are all stand-ins.
- Links already point at the full build's clean URLs (`/services/<slug>/`, `/commercial/`, `/residential/`, `/service-areas/<town>/`, `/projects/`, `/about/`, `/contact/`, `/careers/`, `/faq/`, `/privacy-policy/`, `/terms/`, `/accessibility/`, `/sitemap/`). Until those pages exist, GitHub Pages serves `404.html`, which explains the page is coming in the full build and links back to the homepage and the estimate form. Everything in `404.html` is root-relative because it is served at any depth.
- Project "photos" are elevation drawings (inline SVG) until real project photography is available.
- The logo in `assets/img/` (`logo.svg`, `logo-reverse.svg`, `favicon.svg`) is a temporary mark with text converted to outlines.
- Kept out of search engines on purpose (`noindex` meta + `robots.txt`) until launch.
- `index.html` and `404.html` are assembled from `tools/tpl/` plus generated SVG art (hero wall, elevation drawings, before/after, logo). Edit copy in `tools/tpl/` and re-run `python3 tools/gen.py && python3 tools/assemble.py`. See `tools/README.md`.
