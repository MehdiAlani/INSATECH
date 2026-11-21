# -*- coding: utf-8 -*-
"""Note de synthese INSATECH - BRC-M400 (2 pages A4). Run with system python (PyMuPDF)."""
import os
import sys

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as S  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "01_NOTE_DE_SYNTHESE.pdf"))
T = S.todo

from content_note import HTML


def build():
    arch = pymupdf.Archive(S.FONTS)
    story = pymupdf.Story(html=HTML, user_css=S.DOC_CSS, archive=arch)
    import tempfile
    TMP = os.path.join(tempfile.gettempdir(), "insatech_note_raw.pdf")
    writer = pymupdf.DocumentWriter(TMP)
    MB = pymupdf.paper_rect("a4")
    WHERE = MB + (42, 38, -42, -34)
    n, more = 0, 1
    while more:
        dev = writer.begin_page(MB)
        more, _ = story.place(WHERE)
        story.draw(dev)
        writer.end_page()
        n += 1
    writer.close()
    # page footer
    doc = pymupdf.open(TMP)
    for i, page in enumerate(doc):
        page.draw_line(pymupdf.Point(42, MB.height - 28), pymupdf.Point(MB.width - 42, MB.height - 28),
                       color=(0.79, 0.82, 0.85), width=0.5)
        page.insert_htmlbox(
            pymupdf.Rect(42, MB.height - 26, MB.width - 42, MB.height - 10),
            '<table style="border-collapse:collapse;width:100%%"><tr>'
            '<td style="border:none;padding:0"><small>INSATECH &middot; BRC-M400 Rev C &middot; '
            u'Note de synthèse</small></td>'
            '<td style="border:none;padding:0;text-align:right"><small>%d / %d</small></td>'
            '</tr></table>' % (i + 1, len(doc)),
            css=S.DOC_CSS, archive=arch)
    doc.subset_fonts()
    doc.save(OUT, garbage=4, deflate=True)
    doc.close()
    try:
        os.remove(TMP)
    except OSError:
        pass   # writer may still hold it on Windows; harmless, it is in TEMP
    doc = pymupdf.open(OUT)
    print("note de synthese: %d page(s) -> %s" % (len(doc), OUT))
    for i, p in enumerate(doc):
        p.get_pixmap(dpi=110).save(os.path.join(HERE, "_note_p%d.png" % (i + 1)))
    return len(doc)


if __name__ == "__main__":
    build()
