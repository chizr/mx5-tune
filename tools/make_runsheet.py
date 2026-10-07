from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

VERSION='v10'  # calibration tag this run sheet is for; output goes to docs/run-sheet_<VERSION>.pdf

# Any TTF with the ☐ glyph (U+2610) will do: DejaVu on Linux, Arial Unicode on macOS.
FONTS=['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
       '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
       '/Library/Fonts/Arial Unicode.ttf']
pdfmetrics.registerFont(TTFont('DejaVu',next(f for f in FONTS if os.path.exists(f))))

doc=SimpleDocTemplate(f'docs/run-sheet_{VERSION}.pdf',pagesize=A4,leftMargin=16*mm,rightMargin=16*mm,topMargin=14*mm,bottomMargin=14*mm,
    title=f'MX-5 NB turbo run sheet (cal {VERSION})',author='Chris')
ss=getSampleStyleSheet()
H1=ParagraphStyle('h1',parent=ss['Title'],fontSize=17,spaceAfter=2,alignment=0)
H2=ParagraphStyle('h2',parent=ss['Heading2'],fontSize=12.5,spaceBefore=8,spaceAfter=3,textColor=colors.HexColor('#1f3b57'))
H3=ParagraphStyle('h3',parent=ss['Heading3'],fontSize=10.5,spaceBefore=6,spaceAfter=2)
B=ParagraphStyle('b',parent=ss['BodyText'],fontSize=9,leading=11.5,spaceAfter=2)
S=ParagraphStyle('s',parent=B,fontSize=8,leading=10,textColor=colors.HexColor('#444444'))
C=ParagraphStyle('c',parent=B,fontSize=8.5,leading=10.5,spaceAfter=0)
box='<font name="DejaVu" size="11">☐</font>'
def step(title,lines,note=None):
    out=[Paragraph(title,H3)]
    for l in lines: out.append(Paragraph(f'{box}&nbsp;&nbsp;{l}',B))
    if note: out.append(Paragraph(note,S))
    return out
def grid(header,rows,widths):
    data=[[Paragraph(f'<b>{h}</b>',C) for h in header]]+[[Paragraph(str(c),C) for c in r] for r in rows]
    t=Table(data,colWidths=[w*mm for w in widths],repeatRows=1)
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#999999')),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eef4')),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    return t
st=[]
st.append(Paragraph('MX-5 NB turbo run sheet',H1))
st.append(Paragraph(f'Calibration: <b>mx5_nb_me442.mecal</b> at tag <b>{VERSION}</b> &nbsp;&nbsp; Date: ____________ &nbsp;&nbsp; Ambient: ______ °C &nbsp;&nbsp; Fuel: 98 RON, bought ____________',B))
st.append(Paragraph(f'Part A in the garage, before burning {VERSION}. Part B is everyday driving on the old fuel, <b>off boost</b> (MAP under ~100 kPa), until the tank is low. Part C only on <b>fresh 98</b> and only on a closed road, track day or dyno. Log every drive (all channels, 10 Hz, as on 7 Oct) and note the log number in the box.',S))

st.append(Paragraph('Before you start',H2))
st+= step('',[
 'Save a copy of the calibration currently in the car (v7, for rollback).',
 f'Open {VERSION} in MEITE and spot-check: Ign. Adv. (Pri 1) 83 kPa row at 2000 / 2500 / 3000 / 3500 rpm = 21.25 / 24.25 / 26.75 / 29.5; 97 kPa row = 17.5 / 20.5 / 23.0 / 25.75. Idle OL Duty 80 °C and up = 21.5. Boost Settings: Abs. Max Boost = 190, PWM Min / Max Duty = 0 / 80, PWM Solenoid Control = <b>Normal</b>.',
])

st.append(Paragraph('Part A: garage',H2))
st+= step('A1. Re-plumb the boost solenoid (engine off)',[
 'Photo or label the three hoses as they are now: supply (from boost source), actuator, vent.',
 'Swap the <b>supply</b> and <b>vent</b> hoses at the solenoid. Leave the actuator hose where it is.',
 'Pull the actuator hose off <i>at the actuator</i> so air can come out. Test with 12 V straight across the solenoid (cleaner than MEITE, which caps duty at 80%).',
 '<b>Unpowered:</b> blow into supply. Air comes out of the actuator hose? Y / N',
 '<b>12 V:</b> blow into supply. Blocked? Y / N. Blow into the actuator hose. Comes out of the vent? Y / N',
 'Reconnect the actuator hose. Check all clamps, and that no hose is kinked or touching the turbo.'],
 note='If any answer is N, stop and send the results before driving. Do not "fix" it with PWM Solenoid Control = Inverted: that keeps the unsafe failure mode.')
st+= step('A2. Boost leak test',[
 'Cap the turbo inlet. Pressurise the intake to about 1 bar (15 psi) through a fitting (e.g. a vacuum port or the BOV line).',
 'Listen, and spray soapy water on: compressor outlet, intercooler and its couplers, throttle body, BOV, vacuum lines, PCV, solenoid hoses.',
 'Leaks found and fixed: ______________________________'],
 note='A slow leak-down through the engine itself (open valves) is normal. Hissing at a joint is not.')
st+= step(f'A3. Burn {VERSION}, then warm idle check',[
 f'Burn {VERSION}. Warm fully (coolant 85 °C+).',
 'Fan off, wheel straight: idle ______ rpm (expect ~1,000). Fan on: ______ rpm (expect ~1,050–1,100).'],
 note='Log no: ______')

st.append(Paragraph('Part B: everyday driving on the old fuel (off boost)',H2))
st+= step('B1. Steady cruise for fuelling (VE)',[
 'Hold steady speeds for 10 s or more in 3rd, 4th and 5th, spread across 1,500–4,000 rpm, at light and moderate throttle. A few long steady stretches beat lots of short ones.'],
 note='Log nos: ______ ______ ______')
st+= step('B2. Part-throttle roll-ons (the v8 timing area)',[
 'In 3rd from ~2,000 rpm, moderate throttle up to ~3,000 rpm, staying under ~100 kPa. Three times.',
 'Any knock retard (Ign. Adv. Knock Add below 0)? Y / N &nbsp; At rpm / kPa: ______'],
 note='Log no: ______')
st+= step('B3. Return to idle (baseline, not changed yet)',[
 'A few blips in neutral and a few closed-throttle decels to idle. Lowest rpm seen: ______. Any stall? Y / N. Log no: ______'])

st.append(PageBreak())
st.append(Paragraph('Part C: fresh 98, closed road / track / dyno',H2))
st+= step('C0. Fuel',[
 'Run the tank low, then fill with fresh 98. Write the date at the top. Drive ~20 km before Part C so the new fuel is through.'])
st+= step('C1. Knock runs',[
 'Pull away gently in 1st, three times.',
 'Moderate-throttle roll-on in 3rd from ~1,500 rpm into light boost, three times.',
 'Knock retard seen? Y / N &nbsp; At rpm / kPa: ______'],
 note='Log no: ______')
st+= step('C2. Spring-only boost (0% duty)',[
 'Boost Mode = <b>Manual Duty</b>, PWM Manual Duty = <b>0</b>.',
 'One full-throttle pull in 3rd from ~2,500 to ~5,500 rpm.',
 'Peak MAP: ______ kPa at ______ rpm. Where it levelled off: ______ kPa.',
 'Afterwards, in the log: Boost Final Duty stayed at 0 for the whole pull? Y / N'],
 note='Expect about 135–170 kPa (green spring). If MAP goes past ~175 kPa and keeps rising: lift. The 190 kPa over-boost cut is the backstop. Log no: ______')
st.append(Paragraph('C3. Manual duty steps',H3))
st.append(Paragraph(f'{box}&nbsp;&nbsp;Still in Manual Duty. The same 3rd-gear full-throttle pull at each step. <b>More duty should give more boost.</b> If boost goes <i>down</i> as duty goes up, stop: the plumbing is still wrong. Stop increasing once the peak reaches ~180 kPa (the cut is at 190).',B))
st.append(grid(['Duty %','Peak MAP (kPa)','RPM at peak','Knock retard? (Y/N)','AFR at peak','Log no'],[[d,'','','','',''] for d in ['20','30','40','50','60','']],[22,32,28,34,28,28]))
st.append(Paragraph('Afterwards: Boost Mode back to <b>Closed Loop</b>. Leave the over-boost cut at 190 until the duty tables are set from these results.',S))

st.append(Paragraph('Abort immediately (lift, note the log time) if',H2))
abort=['Oil pressure warning, or the 2,000 rpm oil protection limit trips.',
 'Lean protection trips (3,000 rpm limit), or AFR goes above ~12.5 on boost.',
 'MAP passes ~175 kPa at 0% duty, overshoots a duty step by more than ~15 kPa, or the over-boost cut fires.',
 'Knock retard reaches more than ~3° repeatedly in the same area.',
 'Coolant above ~100 °C or oil above ~120 °C.']
for a in abort: st.append(Paragraph('&bull;&nbsp;&nbsp;'+a,B))

st.append(Paragraph('After each session',H2))
st+= step('',['Copy all logs off and note which log matches which test.',
 'Photograph both pages of this sheet; push the logs and photos to the repo.'])
doc.build(st)
