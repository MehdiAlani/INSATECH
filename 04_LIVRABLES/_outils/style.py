"""Shared look for the INSATECH deliverables (PyMuPDF Story / htmlbox)."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")

NAVY = "#12355B"
BLUE = "#1565C0"
ORANGE = "#BF5700"
GREY = "#5A6672"
RULE = "#C9D2DA"

FACE = """
@font-face {font-family: sg; src: url(segoeui.ttf);}
@font-face {font-family: sg; font-weight: bold; src: url(segoeuib.ttf);}
@font-face {font-family: sg; font-style: italic; src: url(segoeuii.ttf);}
@font-face {font-family: sgl; src: url(segoeuil.ttf);}
"""

# "à confirmer by the mechanical half of the team" marker
TODO = 'span.todo {color: %s; font-style: italic;}' % ORANGE

DOC_CSS = FACE + """
body {font-family: sg; font-size: 9.1px; color: #22282E; line-height: 1.38;}
h1 {font-family: sg; font-size: 15px; color: %(navy)s; margin: 0 0 1px 0;}
h2 {font-family: sg; font-size: 10.2px; color: %(navy)s; margin: 9px 0 3px 0;
    border-bottom: 1px solid %(rule)s; padding-bottom: 1.5px;}
h3 {font-size: 9.1px; color: %(blue)s; margin: 6px 0 1px 0;}
p  {margin: 0 0 4px 0; text-align: justify;}
ul {margin: 0 0 4px 0; padding-left: 12px;}
li {margin: 0 0 1.5px 0;}
b  {color: #10161C;}
small {font-size: 8.1px; color: %(grey)s;}
table {width: 100%%; border-collapse: collapse; margin: 2px 0 5px 0; font-size: 8.5px;}
th {color: %(navy)s; text-align: left; padding: 2.5px 4px; font-weight: bold;
    border-top: 1px solid %(rule)s; border-bottom: 1px solid %(rule)s;}
td {padding: 2.2px 4px; border-bottom: 1px solid #E8EDF2; vertical-align: top;}
td.k {color: %(grey)s; width: 38%%;}
.lead {font-size: 9.4px; color: %(grey)s;}
.tag {background: %(navy)s; color: #FFF; padding: 1px 5px; font-size: 8px;}
%(todo)s
""" % dict(navy=NAVY, blue=BLUE, grey=GREY, rule=RULE, todo=TODO)


def todo(txt):
    return u'<span class="todo">[à compléter — %s]</span>' % txt
