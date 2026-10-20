"""Minimal .pptx writer, standard library only.

Builds a 16:9 deck of blank slides holding rectangles, ellipses, text boxes, pictures and
tables, each slide with speaker notes. Every shape gets a name; the compliance checker
reads `chrome:` names (footer, page number, cover date) as layout, not content.
"""
from __future__ import annotations

import zipfile
from xml.sax.saxutils import escape

EMU = 914400  # per inch
SLIDE_W, SLIDE_H = 12192000, 6858000  # 13.333 x 7.5 in

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def emu(inches: float) -> int:
    return int(round(inches * EMU))


def _x(s) -> str:
    return escape(str(s), {'"': "&quot;"})


class Run:
    def __init__(self, text, size=16, bold=False, italic=False, color="111111", font=None,
                 spacing=None, caps=False):
        self.text, self.size, self.bold, self.italic = text, size, bold, italic
        self.color, self.font, self.spacing, self.caps = color, font, spacing, caps

    def xml(self, default_font: str) -> str:
        attrs = [f'lang="en-US" sz="{int(self.size * 100)}" b="{1 if self.bold else 0}" i="{1 if self.italic else 0}"']
        if self.spacing:
            attrs.append(f'spc="{int(self.spacing * 100)}"')
        if self.caps:
            attrs.append('cap="all"')
        font = _x(self.font or default_font)
        return (f'<a:r><a:rPr {" ".join(attrs)} dirty="0"><a:solidFill><a:srgbClr val="{self.color}"/></a:solidFill>'
                f'<a:latin typeface="{font}"/><a:cs typeface="{font}"/></a:rPr><a:t>{_x(self.text)}</a:t></a:r>')


class Para:
    def __init__(self, runs, align="l", space_after=0, line=None):
        self.runs = runs if isinstance(runs, list) else [runs]
        self.align, self.space_after, self.line = align, space_after, line

    def xml(self, default_font: str) -> str:
        ppr = f'<a:pPr algn="{self.align}">'
        if self.line:
            ppr += f'<a:lnSpc><a:spcPct val="{int(self.line * 100000)}"/></a:lnSpc>'
        ppr += f'<a:spcAft><a:spcPts val="{int(self.space_after * 100)}"/></a:spcAft></a:pPr>'
        size = self.runs[0].size if self.runs else 12
        body = "".join(r.xml(default_font) for r in self.runs)
        return f'<a:p>{ppr}{body}<a:endParaRPr lang="en-US" sz="{int(size * 100)}" dirty="0"/></a:p>'


def _fill(color):
    if color is None:
        return "<a:noFill/>"
    if isinstance(color, tuple):  # vertical gradient
        a, b = color
        return ('<a:gradFill rotWithShape="1"><a:gsLst>'
                f'<a:gs pos="0"><a:srgbClr val="{a}"/></a:gs><a:gs pos="100000"><a:srgbClr val="{b}"/></a:gs>'
                '</a:gsLst><a:lin ang="5400000" scaled="0"/></a:gradFill>')
    return f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'


def _line(color, width_pt=0.75):
    if color is None:
        return "<a:ln><a:noFill/></a:ln>"
    return f'<a:ln w="{int(width_pt * 12700)}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:ln>'


class Slide:
    def __init__(self, font: str):
        self.font = font
        self.shapes: list[str] = []
        self.images: list[bytes] = []
        self.notes = ""
        self.background = None
        self._id = 2

    def _next(self) -> int:
        self._id += 1
        return self._id

    def shape(self, name, x, y, w, h, fill=None, line=None, geom="rect", paras=None, anchor="t",
              inset=0.08, radius=None):
        sid = self._next()
        geom_xml = f'<a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom>'
        if geom == "roundRect" and radius is not None:
            geom_xml = f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val {int(radius)}"/></a:avLst></a:prstGeom>'
        ins = emu(inset)
        if paras:
            body = "".join(p.xml(self.font) for p in paras)
        else:
            body = '<a:p><a:endParaRPr lang="en-US" dirty="0"/></a:p>'
        tx = (f'<p:txBody><a:bodyPr wrap="square" lIns="{ins}" tIns="{ins}" rIns="{ins}" bIns="{ins}" '
              f'anchor="{anchor}" rtlCol="0"><a:noAutofit/></a:bodyPr><a:lstStyle/>{body}</p:txBody>')
        txbox = ' txBox="1"' if fill is None and line is None else ""
        self.shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{_x(name)}"/><p:cNvSpPr{txbox}/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
            f'{geom_xml}{_fill(fill)}{_line(line)}</p:spPr>{tx}</p:sp>')

    def text(self, name, x, y, w, h, paras, anchor="t", inset=0.0):
        self.shape(name, x, y, w, h, fill=None, line=None, paras=paras, anchor=anchor, inset=inset)

    def picture(self, name, png: bytes, x, y, w, h):
        self.images.append(png)
        rid = f"rIdImg{len(self.images)}"
        sid = self._next()
        self.shapes.append(
            f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="{_x(name)}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/>'
            f'</p:cNvPicPr><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch>'
            f'</p:blipFill><p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')

    def table(self, name, x, y, col_widths, row_h, rows, cell_style):
        """rows: list of lists of str. cell_style(r, c) -> dict(fill, color, bold, size, align)."""
        sid = self._next()
        grid = "".join(f'<a:gridCol w="{emu(cw)}"/>' for cw in col_widths)
        trs = []
        for r, row in enumerate(rows):
            tcs = []
            for c, val in enumerate(row):
                st = cell_style(r, c)
                para = Para(Run(val, size=st.get("size", 12), bold=st.get("bold", False),
                                color=st.get("color", "111111")), align=st.get("align", "l"))
                border = ''.join(
                    f'<a:{side} w="6350"><a:solidFill><a:srgbClr val="{st.get("border", "CCCCCC")}"/></a:solidFill></a:{side}>'
                    for side in ("lnL", "lnR", "lnT", "lnB"))
                tcs.append(
                    f'<a:tc><a:txBody><a:bodyPr/><a:lstStyle/>{para.xml(self.font)}</a:txBody>'
                    f'<a:tcPr marL="{emu(0.08)}" marR="{emu(0.08)}" marT="{emu(0.04)}" marB="{emu(0.04)}" anchor="ctr">'
                    f'{border}{_fill(st.get("fill"))}</a:tcPr></a:tc>')
            trs.append(f'<a:tr h="{emu(row_h)}">{"".join(tcs)}</a:tr>')
        total_w = sum(col_widths)
        self.shapes.append(
            f'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="{sid}" name="{_x(name)}"/>'
            '<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr><p:nvPr/></p:nvGraphicFramePr>'
            f'<p:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(total_w)}" cy="{emu(row_h * len(rows))}"/></p:xfrm>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">'
            f'<a:tbl><a:tblPr firstRow="1" bandRow="0"/><a:tblGrid>{grid}</a:tblGrid>{"".join(trs)}</a:tbl>'
            '</a:graphicData></a:graphic></p:graphicFrame>')

    def xml(self) -> str:
        bg = ""
        if self.background is not None:
            bg = f'<p:bg><p:bgPr>{_fill(self.background)}<a:effectLst/></p:bgPr></p:bg>'
        return (f'{XML_HEAD}<p:sld {NS}><p:cSld>{bg}<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/>'
                '</p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/>'
                f'<a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>{"".join(self.shapes)}</p:spTree></p:cSld>'
                '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


def _notes_xml(text: str, font: str) -> str:
    paras = "".join(
        f'<a:p><a:r><a:rPr lang="en-US" sz="1200" dirty="0"><a:latin typeface="{_x(font)}"/></a:rPr>'
        f'<a:t>{_x(line)}</a:t></a:r></a:p>' if line else '<a:p><a:endParaRPr lang="en-US" dirty="0"/></a:p>'
        for line in text.split("\n"))
    return (f'{XML_HEAD}<p:notes {NS}><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/>'
            '</p:nvGrpSpPr><p:grpSpPr/>'
            '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Slide Image Placeholder 1"/><p:cNvSpPr><a:spLocks noGrp="1" noRot="1" noChangeAspect="1"/></p:cNvSpPr>'
            '<p:nvPr><p:ph type="sldImg"/></p:nvPr></p:nvSpPr><p:spPr/></p:sp>'
            '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/>{paras}</p:txBody></p:sp></p:spTree></p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>')


def _theme(name: str, colors: dict, font: str) -> str:
    c = colors
    return (f'{XML_HEAD}<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="{_x(name)}">'
            f'<a:themeElements><a:clrScheme name="{_x(name)}">'
            f'<a:dk1><a:srgbClr val="{c["gray_800"]}"/></a:dk1><a:lt1><a:srgbClr val="{c["white"]}"/></a:lt1>'
            f'<a:dk2><a:srgbClr val="{c["gray_700"]}"/></a:dk2><a:lt2><a:srgbClr val="{c["gray_100"]}"/></a:lt2>'
            f'<a:accent1><a:srgbClr val="{c["green"]}"/></a:accent1><a:accent2><a:srgbClr val="{c["green_dark"]}"/></a:accent2>'
            f'<a:accent3><a:srgbClr val="{c["green_70"]}"/></a:accent3><a:accent4><a:srgbClr val="{c["green_40"]}"/></a:accent4>'
            f'<a:accent5><a:srgbClr val="{c["gray_400"]}"/></a:accent5><a:accent6><a:srgbClr val="{c["gray_300"]}"/></a:accent6>'
            f'<a:hlink><a:srgbClr val="{c["green_dark"]}"/></a:hlink><a:folHlink><a:srgbClr val="{c["gray_400"]}"/></a:folHlink>'
            f'</a:clrScheme><a:fontScheme name="{_x(name)}"><a:majorFont><a:latin typeface="{_x(font)}"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
            f'<a:minorFont><a:latin typeface="{_x(font)}"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>'
            '<a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
            '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>'
            '<a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
            '<a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
            '<a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>'
            '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle>'
            '<a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
            '<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
            '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements>'
            '<a:objectDefaults/><a:extraClrSchemeLst/></a:theme>')


_CLRMAP = ('<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" '
           'accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>')
_EMPTY_TREE = ('<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
               '<p:grpSpPr/></p:spTree>')


def _rels(items) -> str:
    body = "".join(f'<Relationship Id="{i}" Type="{t}" Target="{_x(tg)}"/>' for i, t, tg in items)
    return f'{XML_HEAD}<Relationships xmlns="{PKG_REL}">{body}</Relationships>'


def save(path, slides: list[Slide], colors: dict, font: str, title: str, author: str, created_iso: str) -> None:
    n = len(slides)
    ct = ['<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
          '<Default Extension="xml" ContentType="application/xml"/>',
          '<Default Extension="png" ContentType="image/png"/>',
          '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
          '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
          '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
          '<Override PartName="/ppt/notesMasters/notesMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"/>',
          '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
          '<Override PartName="/ppt/theme/theme2.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
          '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
          '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>']
    for i in range(1, n + 1):
        ct.append(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
        ct.append(f'<Override PartName="/ppt/notesSlides/notesSlide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>')
    files = {
        "[Content_Types].xml": f'{XML_HEAD}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">{"".join(ct)}</Types>',
        "_rels/.rels": _rels([
            ("rId1", f"{REL}/officeDocument", "ppt/presentation.xml"),
            ("rId2", "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties", "docProps/core.xml"),
            ("rId3", f"{REL}/extended-properties", "docProps/app.xml")]),
        "docProps/core.xml": (
            f'{XML_HEAD}<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{_x(title)}</dc:title><dc:creator>{_x(author)}</dc:creator>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{created_iso}</dcterms:created></cp:coreProperties>'),
        "docProps/app.xml": (
            f'{XML_HEAD}<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
            f'<Application>blueprint-deck</Application><Slides>{n}</Slides><Notes>{n}</Notes></Properties>'),
        "ppt/theme/theme1.xml": _theme("WISE", colors, font),
        "ppt/theme/theme2.xml": _theme("WISE Notes", colors, font),
        "ppt/slideMasters/slideMaster1.xml": (
            f'{XML_HEAD}<p:sldMaster {NS}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg>'
            f'{_EMPTY_TREE}</p:cSld>{_CLRMAP}<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
            '<p:txStyles><p:titleStyle><a:lvl1pPr><a:defRPr sz="3200"/></a:lvl1pPr></p:titleStyle>'
            '<p:bodyStyle><a:lvl1pPr><a:defRPr sz="1600"/></a:lvl1pPr></p:bodyStyle>'
            '<p:otherStyle><a:lvl1pPr><a:defRPr sz="1400"/></a:lvl1pPr></p:otherStyle></p:txStyles></p:sldMaster>'),
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": _rels([
            ("rId1", f"{REL}/slideLayout", "../slideLayouts/slideLayout1.xml"),
            ("rId2", f"{REL}/theme", "../theme/theme1.xml")]),
        "ppt/slideLayouts/slideLayout1.xml": (
            f'{XML_HEAD}<p:sldLayout {NS} type="blank" preserve="1"><p:cSld name="Blank">{_EMPTY_TREE}</p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>'),
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels": _rels([
            ("rId1", f"{REL}/slideMaster", "../slideMasters/slideMaster1.xml")]),
        "ppt/notesMasters/notesMaster1.xml": (
            f'{XML_HEAD}<p:notesMaster {NS}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg>'
            f'{_EMPTY_TREE}</p:cSld>{_CLRMAP}</p:notesMaster>'),
        "ppt/notesMasters/_rels/notesMaster1.xml.rels": _rels([
            ("rId1", f"{REL}/theme", "../theme/theme2.xml")]),
    }
    sld_ids = "".join(f'<p:sldId id="{256 + i}" r:id="rId{i + 10}"/>' for i in range(1, n + 1))
    files["ppt/presentation.xml"] = (
        f'{XML_HEAD}<p:presentation {NS} saveSubsetFonts="1">'
        '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
        '<p:notesMasterIdLst><p:notesMasterId r:id="rId2"/></p:notesMasterIdLst>'
        f'<p:sldIdLst>{sld_ids}</p:sldIdLst><p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}"/>'
        '<p:notesSz cx="6858000" cy="9144000"/><p:defaultTextStyle/></p:presentation>')
    pres_rels = [("rId1", f"{REL}/slideMaster", "slideMasters/slideMaster1.xml"),
                 ("rId2", f"{REL}/notesMaster", "notesMasters/notesMaster1.xml"),
                 ("rId3", f"{REL}/theme", "theme/theme1.xml")]
    pres_rels += [(f"rId{i + 10}", f"{REL}/slide", f"slides/slide{i}.xml") for i in range(1, n + 1)]
    files["ppt/_rels/presentation.xml.rels"] = _rels(pres_rels)

    media: dict[str, bytes] = {}
    for i, s in enumerate(slides, 1):
        files[f"ppt/slides/slide{i}.xml"] = s.xml()
        rels = [("rId1", f"{REL}/slideLayout", "../slideLayouts/slideLayout1.xml"),
                ("rId2", f"{REL}/notesSlide", f"../notesSlides/notesSlide{i}.xml")]
        for k, png in enumerate(s.images, 1):
            name = f"image{i}_{k}.png"
            media[f"ppt/media/{name}"] = png
            rels.append((f"rIdImg{k}", f"{REL}/image", f"../media/{name}"))
        files[f"ppt/slides/_rels/slide{i}.xml.rels"] = _rels(rels)
        files[f"ppt/notesSlides/notesSlide{i}.xml"] = _notes_xml(s.notes, font)
        files[f"ppt/notesSlides/_rels/notesSlide{i}.xml.rels"] = _rels([
            ("rId1", f"{REL}/notesMaster", "../notesMasters/notesMaster1.xml"),
            ("rId2", f"{REL}/slide", f"../slides/slide{i}.xml")])

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", files.pop("[Content_Types].xml"))
        for name, data in files.items():
            z.writestr(name, data)
        for name, data in media.items():
            z.writestr(name, data)
