# tools/: regenerate the SVG art and the two HTML pages

Not a build step. The site is plain static files; run these by hand when the art or a shared partial changes, then commit the regenerated output.

```sh
python3 tools/gen.py        # art → tools/frag/ (git-ignored) + assets/img/logo.svg, logo-reverse.svg, favicon.svg
python3 tools/assemble.py   # tools/tpl/* + tools/frag/* → index.html, 404.html
```

Python 3.8+, standard library only. Paths are relative to this folder, so they work from any working directory.

## What's where

- `gen.py` writes the generated art.
  - Hero wall: retones and textures the base geometry in `src/wall-base.svg`.
  - Elevation drawings: the three project plates. Their linework classes are styled in `css/styles.css` under `.dwg`.
  - Before/after illustration.
  - Logo mark: the header symbol, both logo files and the favicon.
- `assemble.py` fills each `@@name@@` marker in `tpl/` with the matching fragment.
  - `header.html` and `footer.html` are shared by both pages.
  - `@@ROOT@@` becomes `""` in index.html and `/` in 404.html, which is served at any depth.
- `tpl/`: the page templates. **Edit page copy here, not in the generated index.html or 404.html**, or the next assemble will overwrite it.
- `src/` holds hand-made sources that are copied in as-is: the lighthouse, service-area map, icon sprite symbols, v1 wall geometry, and the outlined logo text.

CSS and JS (`css/styles.css`, `js/main.js`) are edited directly; nothing here touches them.
