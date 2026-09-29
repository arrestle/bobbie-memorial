// Memorial slideshow builder. Usage: node build_deck.js manifest.json out.pptx
// Manifest format: see ../references/deck-manifest.md
// look for pptxgenjs next to this script, then in the current folder (npm install pptxgenjs there)
let pptxgen;
try { pptxgen = require('pptxgenjs'); } catch (e) { pptxgen = require(require.resolve('pptxgenjs', { paths: [process.cwd()] })); }
const fs = require('fs');
const M = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const OUT = process.argv[3];
// image paths in the manifest are relative to the manifest file
const path = require('path');
const BASE = path.dirname(path.resolve(process.argv[2]));
(function fix(o) {
  if (Array.isArray(o)) return o.forEach(fix);
  if (o && typeof o === 'object') {
    if (typeof o.img === 'string' && !path.isAbsolute(o.img)) o.img = path.join(BASE, o.img);
    Object.values(o).forEach(fix);
  }
})(M);

const C = Object.assign({ dark: '1F3A2E', gold: 'C9A461', light: 'F2EFE8', ink: '2B2B2B', body: '444444', muted: '707070', white: 'FFFFFF' }, M.colors || {});
const HEAD = 'Cambria', BODY = 'Calibri';
const W = 13.333;

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.title = M.title + (M.subtitle ? ': ' + M.subtitle : '');

function fit(p, bx, by, bw, bh) {
  const r = Math.min(bw / p.w, bh / p.h), w = p.w * r, h = p.h * r;
  return { x: bx + (bw - w) / 2, y: by + (bh - h) / 2, w, h };
}
const shadow = () => ({ type: 'outer', color: '000000', opacity: 0.28, blur: 8, offset: 3, angle: 45 });
function photo(slide, p, bx, by, bw, bh) {
  if (!p) return;
  const f = fit(p, bx, by, bw, bh);
  slide.addImage({ path: p.img, x: f.x, y: f.y, w: f.w, h: f.h, shadow: shadow(), altText: p.title || '' });
}
function lines(text, widthIn, pt) {  // rough wrap estimate (Calibri ~0.5 em average)
  const perLine = Math.max(8, Math.floor(widthIn / (pt * 0.5 / 72)));
  return text.split('\n').reduce((n, s) => n + Math.max(1, Math.ceil(s.length / perLine)), 0);
}
const notes = (sl, p) => sl.addNotes([p.date + ' — ' + p.title, p.caption, p.source, p.notes].filter(Boolean).join('\n\n'));
const footer = (sl, sec, p) => sl.addText(sec.name + (p.source ? '  ·  ' + p.source : ''), { x: 1.0, y: 7.15, w: 11.3, h: 0.25, fontFace: BODY, fontSize: 9, color: C.muted, align: 'center', margin: 0, isTextBox: true });
function heading(sl, p, y, pt) {
  const t = [{ text: p.date, options: { fontFace: HEAD, bold: true, color: C.dark } }];
  if (p.estimated) t.push({ text: ' (estimated)', options: { italic: true, color: C.muted, fontSize: 12 } });
  t.push({ text: '   ' + p.title, options: { fontFace: BODY, bold: true, color: C.ink } });
  sl.addText(t, { x: 1.0, y, w: 11.3, h: 0.35 * pt / 16, fontSize: pt, align: 'center', valign: 'top', margin: 0, isTextBox: true });
}

// ---- title slide
{
  const s = pres.addSlide(); s.background = { color: C.dark };
  s.addText(M.title, { x: 0.8, y: 1.6, w: 6.6, h: 2.2, fontFace: HEAD, fontSize: 44, bold: true, color: C.white, valign: 'top', margin: 0, isTextBox: true });
  if (M.years) s.addText(M.years, { x: 0.8, y: 3.95, w: 6.6, h: 0.6, fontFace: HEAD, fontSize: 26, color: C.gold, margin: 0, isTextBox: true });
  if (M.subtitle) s.addText(M.subtitle, { x: 0.8, y: 4.75, w: 5.8, h: 1.1, fontFace: BODY, fontSize: 17, color: C.light, margin: 0, valign: 'top', isTextBox: true });
  photo(s, M.cover, 8.3, 0.6, 4.4, 6.3);
}

// ---- chapters
M.sections.forEach((sec, si) => {
  const s = pres.addSlide(); s.background = { color: C.dark };
  s.addText('PART ' + (si + 1), { x: 0.8, y: 1.3, w: 6, h: 0.5, fontFace: BODY, fontSize: 16, bold: true, charSpacing: 4, color: C.gold, margin: 0, isTextBox: true });
  s.addText(sec.name, { x: 0.8, y: 1.9, w: 6.4, h: 2.0, fontFace: HEAD, fontSize: 38, bold: true, color: C.white, valign: 'top', margin: 0, isTextBox: true });
  if (sec.summary) s.addText(sec.summary, { x: 0.8, y: 4.1, w: 6.0, h: 1.8, fontFace: BODY, fontSize: 17, color: C.light, valign: 'top', margin: 0, isTextBox: true });
  s.addText(sec.photos.length + ' photographs', { x: 0.8, y: 6.2, w: 4, h: 0.4, fontFace: BODY, fontSize: 13, italic: true, color: C.gold, margin: 0, isTextBox: true });
  photo(s, sec.key || sec.photos[0], 7.6, 0.8, 5.0, 5.9);

  for (const p of sec.photos) {
    const sl = pres.addSlide(); sl.background = { color: C.white };
    const imgs = p.imgs || [p];
    if (imgs.length > 1) {
      // pair / triple: pieces side by side, centred, labels under each
      const gap = 0.4, boxH = 5.1, boxW = (W - 1.6 - gap * (imgs.length - 1)) / imgs.length;
      const fs_ = imgs.map(im => fit(im, 0, 0.3, boxW, boxH));
      let x = (W - (fs_.reduce((a, f) => a + f.w, 0) + gap * (imgs.length - 1))) / 2;
      imgs.forEach((im, i) => {
        const f = fs_[i];
        sl.addImage({ path: im.img, x, y: f.y, w: f.w, h: f.h, shadow: shadow(), altText: (p.title || '') + (im.label ? ' — ' + im.label : '') });
        if (im.label) sl.addText(im.label, { x, y: f.y + f.h + 0.05, w: f.w, h: 0.25, fontFace: BODY, fontSize: 11, italic: true, color: C.muted, align: 'center', margin: 0, isTextBox: true });
        x += f.w + gap;
      });
      const ty = Math.max(...fs_.map(f => f.y + f.h)) + 0.4;
      heading(sl, p, ty, 16);
      if (p.caption) sl.addText(p.caption, { x: 1.0, y: ty + 0.4, w: 11.3, h: 7.1 - ty - 0.4, fontFace: BODY, fontSize: 13, color: C.body, align: 'center', valign: 'top', margin: 0, isTextBox: true });
    } else {
      // single: large centred photo, date + title line, caption
      const boxH = p.caption ? 5.35 : 5.75;
      const f = fit(p, 0.5, 0.3, W - 1.0, boxH);
      sl.addImage({ path: p.img, x: f.x, y: f.y, w: f.w, h: f.h, shadow: shadow(), altText: p.title || '' });
      let ty = f.y + f.h + 0.18;
      const headLen = (p.date || '').length + (p.title || '').length + 3;
      let hpt = 18; while (lines('x'.repeat(headLen), 11.3, hpt) > 1 && hpt > 12) hpt--;
      const hh = lines('x'.repeat(headLen), 11.3, hpt) * hpt * 1.25 / 72 + 0.05;
      heading(sl, p, ty, hpt); ty += hh + 0.05;
      if (p.caption) {
        const avail = 7.1 - ty;
        let cpt = 14; while (lines(p.caption, 11.3, cpt) * cpt * 1.3 / 72 > avail && cpt > 10) cpt--;
        sl.addText(p.caption, { x: 1.0, y: ty, w: 11.3, h: avail, fontFace: BODY, fontSize: cpt, color: C.body, align: 'center', valign: 'top', margin: 0, isTextBox: true });
      }
    }
    footer(sl, sec, p); notes(sl, p);
  }
});

// ---- closing slide
if (M.closing) {
  const s = pres.addSlide(); s.background = { color: C.dark };
  s.addText(M.closing.title, { x: 0.8, y: 0.8, w: 11.7, h: 0.9, fontFace: HEAD, fontSize: 38, bold: true, color: C.white, margin: 0, isTextBox: true });
  (M.closing.stats || []).slice(0, 3).forEach(([big, txt], i) => {
    const x = 0.8 + i * 4.05;
    s.addText(big, { x, y: 2.4, w: 3.6, h: 1.3, fontFace: HEAD, fontSize: 64, bold: true, color: C.gold, margin: 0, isTextBox: true });
    s.addText(txt, { x, y: 3.8, w: 3.5, h: 1.8, fontFace: BODY, fontSize: 15, color: C.light, valign: 'top', margin: 0, isTextBox: true });
  });
  if (M.closing.footnote) s.addText(M.closing.footnote, { x: 0.8, y: 6.5, w: 11.7, h: 0.4, fontFace: BODY, fontSize: 11, italic: true, color: C.gold, margin: 0, isTextBox: true });
}

pres.writeFile({ fileName: OUT }).then(f => console.log('wrote', f));
