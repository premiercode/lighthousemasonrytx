"""Assemble index.html and 404.html from tools/tpl + tools/frag (run tools/gen.py first)."""
import os, re

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)


def rd(*p):
    return open(os.path.join(TOOLS, *p)).read()


frags = {fn.rsplit('.', 1)[0]: rd('frag', fn).rstrip('\n') for fn in os.listdir(os.path.join(TOOLS, 'frag'))}
frags['mark'] = frags['mark-symbol']
frags['header'] = rd('tpl', 'header.html').rstrip('\n')
frags['footer'] = rd('tpl', 'footer.html').rstrip('\n')


def build(tpl, out, root):
    t = rd('tpl', tpl)
    for _ in range(2):  # partials may contain markers
        t = re.sub(r'@@([a-z0-9-]+)@@', lambda m: frags[m.group(1)], t)
    t = t.replace('@@ROOT@@', root)
    assert '@@' not in t, re.findall(r'@@\w+@@', t)
    open(os.path.join(REPO, out), 'w').write(t)
    print(out, len(t))


build('index.html', 'index.html', '')
build('404.html', '404.html', '/')
