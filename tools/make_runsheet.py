from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))

doc=SimpleDocTemplate('docs/run-sheet_v7.pdf',pagesize=A4,leftMargin=16*mm,rightMargin=16*mm,topMargin=14*mm,bottomMargin=14*mm,
    title='MX-5 NB turbo run sheet (cal v7)',author='Chris')
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
st.append(Paragraph('Calibration: <b>18Jul_boost_pwm_limits_v7.mecal</b> &nbsp;&nbsp; Date: ____________ &nbsp;&nbsp; Ambient: ______ °C &nbsp;&nbsp; Fuel: 98 RON',B))
st.append(Paragraph('Do Part A in the driveway first. Part B needs the car moving; keep the boost pulls (B4, B5) for a closed road, track day or the dyno. Start a fresh log for each test and note the log number in the box.',S))

st.append(Paragraph('Before you start',H2))
st+= step('',[
 'Save a copy of the calibration currently in the car (rollback).',
 'Open v7 in MEITE and spot-check: dead time axis shows 12.5 / 13.25 / 13.5 / 13.75 V cells; lean protection triggers on <i>leaner</i> than target; oil protection on with the 130–240 kPa table.',
 'Enable logging of: knock cyl 1–4 peak and event count, knock reading peak, knock add, overrun status, extra idle load switch, fan status, idle target / error / P / I, boost P / I / CL init duty, EPS status channels.',
 'Burn v7. Check the actuator and solenoid hoses and clamps.',
])

st.append(Paragraph('Part A: driveway (stationary)',H2))
st+= step('A1. Cold start: IAT check',[
 'Before starting a cold engine, compare IAT reading to ambient. IAT: ______ °C, ambient: ______ °C (should be within 1–2 °C).',
 'Note the IAT sensor body: open element / brass closed: __________'])
st+= step('A2. Warm up, then knock sensor tap test',[
 'Warm fully (coolant 85 °C+). Note when the fan cycles (on 92 °C, off 89 °C).',
 'At idle, tap the block near the knock sensor lightly with a spanner. Knock reading jumps? Y / N'])
st+= step('A3. Power steering switch',[
 'At warm idle, turn the wheel to full lock and hold. Extra load switch status changes? Y / N. Idle duty rises ~6%? Y / N',
 'If it never changes: check switch and wiring. If it is stuck on: active state is inverted.'])
st.append(KeepTogether(step('A4. Idle voltage test (dead times)',[
 'Temporarily disable closed loop lambda. Fan off. Wheel straight.',
 'Log ~2 min while switching headlights, rear demister, then all together, 20 s each. Watch AFR vs battery voltage.',
 'AFR steady as voltage moves = good. Leaner when voltage drops = low-voltage dead times too short; richer = too long.',
 'Re-enable closed loop lambda.'],
 note='Log no: ______')))
st.append(Paragraph('A5. Idle valve duty sweep',H3))
st.append(Paragraph(f'{box}&nbsp;&nbsp;Fan off, wheel straight, closed loop lambda on. Set idle to manual duty (or edit the warm cell live). Hold each step ~15 s, then record. Stop and raise duty if rpm falls below ~850.',B))
st.append(grid(['Duty %','30','27','25','23','21','19','17'],[['RPM','','','','','','',''],['MAP kPa','','','','','','',''],['AFR','','','','','','','']],[22]+[22]*7))
st.append(Paragraph('If rpm stops falling below some duty: extra air is setting the floor (throttle stop, idle air screw, vacuum leak, BOV). Restore open loop idle afterwards. Log no: ______',S))
st+= step('A6. Idle spark scatter (optional, do last)',[
 'Set spark scatter to about +3° at −300 rpm error and −3° at +300 rpm (0 at 0). Confirm the sign: with rpm below target the ECU must <i>add</i> advance.',
 'Blip the throttle a few times; return to idle should be smoother, not oscillating. If it hunts, reduce or remove.'])

st.append(PageBreak())
st.append(Paragraph('Part B: on the road',H2))
st+= step('B1. Overrun and return to idle',[
 'Six to eight decels from 3,000–4,000 rpm to idle in gear, throttle fully closed; then three with the clutch in.',
 'Feel for droop or stumble on the way to idle. Lowest rpm seen: ______. Any stall? Y / N'],
 note='Expected: fuel cut on decel (overrun status), fuel back in at 1,800 rpm, lambda trim not winding up to +20%. Log no: ______')
st+= step('B2. Knock baseline (off boost)',[
 'Steady moderate-throttle cruising in 3rd and 4th across as much of 1,500–6,000 rpm as is legal, staying below ~95 kPa.',
 'Knock add should stay at 0. Any knock retard during gentle cruise = threshold too low, note rpm: ______'],
 note='Log no: ______')
st+= step('B3. Knock reproduction',[
 'Pull away gently in 1st, three times.',
 'Moderate-throttle roll-on in 3rd from ~1,500 rpm into light boost, three times.',
 'Note any knock retard and which cylinder peaks rise: ______'],
 note='Log no: ______')
st+= step('B4. Wastegate solenoid unplugged (closed road / track)',[
 'Unplug the solenoid. One full-throttle pull in 3rd from ~2,500 rpm.',
 'Peak MAP: ______ kPa. Should be spring pressure only (around 150 kPa). If it keeps rising: lift, and check solenoid plumbing.'],
 note='Over-boost cut (225 kPa) is the backstop. Log no: ______')
st.append(Paragraph('B5. Open loop boost duty steps (closed road / track / dyno)',H3))
st.append(Paragraph(f'{box}&nbsp;&nbsp;Boost mode = Open Loop, flat duty table. For each step set over-boost cut ~20 kPa above the previous step\'s peak. Full-throttle 3rd-gear pull ~2,500–6,500 rpm. Stop increasing duty once peak reaches ~190 kPa.',B))
st.append(grid(['Duty %','Cut set (kPa)','Peak MAP (kPa)','RPM at peak','Knock add? (Y/N)','Log no'],[[d,'','','','',''] for d in ['0','20','30','40','50','']],[22,30,32,28,32,28]))
st.append(Paragraph('Afterwards: set boost mode back to Closed Loop and over-boost cut back to 225 kPa.',S))

st.append(Paragraph('Abort immediately (lift, note the log time) if',H2))
abort=['Oil pressure warning or the 2,000 rpm oil protection limit trips.',
 'Lean protection trips (3,000 rpm limit), or AFR goes above ~12.5 on boost.',
 'MAP overshoots the expected value by more than ~15 kPa, or the over-boost cut fires unexpectedly.',
 'Knock retard reaches more than ~3° repeatedly in the same area.',
 'Coolant above ~100 °C or oil above ~120 °C.']
for a in abort: st.append(Paragraph('&bull;&nbsp;&nbsp;'+a,B))

st.append(Paragraph('After the drive',H2))
st+= step('',['Copy all logs off the SD card; note which log matches which test.',
 'Upload the logs, the calibration that was in the car, and filled-in copies of A5 / B4 / B5 to the next chat with the worklog link.'])
doc.build(st)
