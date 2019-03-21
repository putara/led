import math
import sys
import os
import re
import getopt
import string
import fontforge

re_comment = re.compile(r'^#')
re_char = re.compile(r'^\:([0-9A-Fa-f]{2,6}|\.[\w]+)')
re_lcd = re.compile(r'^([\*-\.]{5})')

cfg = dict(cell = 24, duty = 3, condense = 100, offset = 1, space = 4)
met = dict(xcell = 0, ycell = 0, xgap = 0, ygap = 0, xoffset = 0, yoffset = 0, xspace = 0, yspace = 0, ascent = 0, descent = 0, svgwidth  = 0, svgheight = 0)
outdir = 'bin'
ledtxt = 'led.txt'

try:
    os.mkdir(outdir)
except OSError as e:
    pass

ff = fontforge.open('led.sfd')

def ishexdigits(s):
    return all(c in string.hexdigits for c in s)

def addglyph(cp, dots):
    if cp == '':
        return
    empty = True
    svgfile = os.path.join(outdir, '~ledtmp.svg')
    fp = open(svgfile, 'w')
    fp.write('<svg xmlns:svg="http://www.w3.org/2000/svg" viewBox="0 0 {0} {1}">'.format(met['svgwidth'], met['svgheight']))
    for k, v in dots.items():
        x = k % 5
        y = k / 5
        if v:
            x1 = met['xoffset'] + (met['xgap'] + met['xcell']) * x
            y1 = met['yoffset'] + (met['ygap'] + met['ycell']) * y
            x2 = x1 + met['xcell']
            y2 = y1 + met['ycell']
            fp.write('  <path d="M {0},{1} V {3} H {2} V {1} Z"/>'.format(x1, y1, x2, y2))
            empty = False
    fp.write('</svg>')
    fp.close()
    if ishexdigits(cp):
        ch = ff.createChar(int(cp, 16))
    else:
        ch = ff.createChar(-1, cp)
    ch.clear()
    ch.width = met['svgwidth']
    ch.vwidth = met['svgheight']
    if not empty:
        ch.importOutlines(svgfile, ('removeoverlap', 'correctdir'))
    try:
        os.remove(svgfile)
    except OSError as e:
        print('cannot remove: %s' % svgfile)
        pass

def usage():
    print('ffpython led.py [-h][-s size][-d duty][-c condense][-f offset][-l space][-o outdir] [led.txt]')

def init():
    global cfg, met, outdir, ledtxt

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hs:d:c:f:l:o:')
    except getopt.GetoptError as err:
        print str(err)
        usage()
        return False

    for o, a in opts:
        if o == '-h':
            usage()
            return ''
        if o == '-s':
            cfg['cell'] = int(a)
        if o == '-d':
            cfg['duty'] = float(a)
        if o == '-c':
            cfg['condense'] = float(a)
        if o == '-f':
            cfg['offset'] = float(a)
        if o == '-l':
            cfg['space'] = float(a)
        if o == '-o':
            outdir = a

    met['xcell'] = cfg['cell'] * cfg['duty'] * (0.01 * cfg['condense'])
    met['ycell'] = cfg['cell'] * cfg['duty']
    met['xgap'] = cfg['cell'] * (0.01 * cfg['condense'])
    met['ygap'] = cfg['cell']
    met['xoffset'] = met['xgap'] * cfg['offset']
    met['yoffset'] = met['ygap'] * cfg['offset']
    met['xspace'] = met['xgap'] * cfg['space']
    met['yspace'] = met['ygap'] * cfg['space']
    met['ascent'] = met['yoffset'] + (met['ygap'] + met['ycell']) * 7
    met['descent'] = met['yspace']
    met['svgwidth']  = met['xoffset'] + (met['xgap'] + met['xcell']) * 5 + met['xspace']
    met['svgheight'] = met['ascent'] + met['descent']

    if len(args) > 0:
        ledtxt = args[0]
    return True

def main():
    if not init():
        return

    ff.ascent = met['ascent']
    ff.descent = met['descent']
    ff.weight = 'Regular'
    ff.version = '1.00'
    ff.comment = '-s %d -d %g -c %g -f %g -l %g' % (cfg['cell'], cfg['duty'], cfg['condense'], cfg['offset'], cfg['space'])
    ff.os2_winascent_add = 0
    ff.os2_windescent_add = 0
    ff.hhea_ascent_add = 0
    ff.hhea_descent_add = 0
    ff.os2_winascent = met['ascent']
    ff.os2_windescent = met['descent']
    ff.hhea_ascent = met['ascent']
    ff.hhea_descent = -met['descent']
    ff.hhea_linegap = met['yspace']

    cp = ''
    y = 0
    dots = {}
    fp = open(ledtxt, 'r')
    for line in fp:
        if re_comment.match(line):
            continue
        m = re_char.match(line)
        if m:
            addglyph(cp, dots)
            y = 0
            cp = m.group(1)
            dots = {}
            continue
        m = re_lcd.match(line)
        if m:
            m = m.group(0)
            for x in range(0, 5):
                dots[y * 5 + x] = m[x] == '*'
            y += 1
    fp.close()
    addglyph(cp, dots)
    ff.save(os.path.join(outdir, 'led-ff.sfd'))
    ff.generate(os.path.join(outdir, 'led.ttf'), '', ('short-post', 'opentype', 'PfEd-lookups'))

if __name__ == '__main__':
    main()
