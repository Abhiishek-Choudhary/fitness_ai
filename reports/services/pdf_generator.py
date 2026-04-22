"""Generate professional PDF fitness reports using ReportLab."""
import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable


# ── Brand colours ──────────────────────────────────────────────────────────────
PRIMARY = colors.HexColor('#6366f1')     # indigo
ACCENT = colors.HexColor('#10b981')      # emerald
WARNING = colors.HexColor('#f59e0b')     # amber
DANGER = colors.HexColor('#ef4444')      # red
LIGHT_BG = colors.HexColor('#f8fafc')
CARD_BG = colors.HexColor('#f1f5f9')
TEXT_DARK = colors.HexColor('#1e293b')
TEXT_MUTED = colors.HexColor('#64748b')
WHITE = colors.white


def _styles():
    base = getSampleStyleSheet()
    return {
        'title': ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=28,
                                textColor=WHITE, alignment=TA_CENTER, spaceAfter=4),
        'subtitle': ParagraphStyle('subtitle', fontName='Helvetica', fontSize=13,
                                   textColor=WHITE, alignment=TA_CENTER, spaceAfter=2),
        'section': ParagraphStyle('section', fontName='Helvetica-Bold', fontSize=14,
                                  textColor=PRIMARY, spaceBefore=14, spaceAfter=6),
        'body': ParagraphStyle('body', fontName='Helvetica', fontSize=10,
                               textColor=TEXT_DARK, spaceAfter=4, leading=15),
        'muted': ParagraphStyle('muted', fontName='Helvetica', fontSize=9,
                                textColor=TEXT_MUTED, spaceAfter=3),
        'bold': ParagraphStyle('bold', fontName='Helvetica-Bold', fontSize=10,
                               textColor=TEXT_DARK, spaceAfter=4),
        'ai_body': ParagraphStyle('ai_body', fontName='Helvetica', fontSize=10,
                                  textColor=TEXT_DARK, leading=16, spaceAfter=5),
        'ai_heading': ParagraphStyle('ai_heading', fontName='Helvetica-Bold', fontSize=11,
                                     textColor=PRIMARY, spaceBefore=10, spaceAfter=4),
        'metric_label': ParagraphStyle('metric_label', fontName='Helvetica', fontSize=8,
                                       textColor=TEXT_MUTED, alignment=TA_CENTER),
        'metric_value': ParagraphStyle('metric_value', fontName='Helvetica-Bold', fontSize=20,
                                       textColor=PRIMARY, alignment=TA_CENTER),
    }


def _stat_card(label: str, value: str, unit: str = '', color=None) -> Table:
    s = _styles()
    c = color or PRIMARY
    val_style = ParagraphStyle('mv', fontName='Helvetica-Bold', fontSize=18,
                               textColor=c, alignment=TA_CENTER)
    t = Table(
        [[Paragraph(str(value) + (f' {unit}' if unit else ''), val_style)],
         [Paragraph(label, s['metric_label'])]],
        colWidths=[4.2 * cm],
    )
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CARD_BG),
        ('ROUNDEDCORNERS', [6]),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def _section_header(text: str, s: dict):
    return [
        Paragraph(text, s['section']),
        HRFlowable(width='100%', thickness=1.5, color=PRIMARY, spaceAfter=6),
    ]


def _cover_page(story, data: dict, period: str, period_start: str, period_end: str, s: dict):
    # Header banner (simulated with a coloured table)
    banner = Table(
        [[Paragraph('FitnessAI', s['title'])],
         [Paragraph(f'{period.upper()} PERFORMANCE REPORT', s['subtitle'])],
         [Paragraph(f'{period_start}  →  {period_end}', s['subtitle'])]],
        colWidths=[17 * cm],
    )
    banner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ('ROUNDEDCORNERS', [8]),
    ]))
    story.append(banner)
    story.append(Spacer(1, 0.8 * cm))

    # User info card
    profile = data['profile']
    user = data['user']
    info_rows = [
        ['Name', user['name']],
        ['Email', user['email']],
        ['Age / Gender', f"{profile.get('age', '—')} / {profile.get('gender', '—').capitalize()}"],
        ['Height / Weight', f"{profile.get('height_cm', '—')} cm / {profile.get('weight_kg', '—')} kg"],
        ['Fitness Goal', (profile.get('fitness_goal') or '—').replace('_', ' ').title()],
        ['Fitness Level', (profile.get('fitness_level') or '—').title()],
        ['Activity Level', (profile.get('activity_level') or '—').title()],
    ]
    user_table = Table(
        [[Paragraph(r[0], s['muted']), Paragraph(str(r[1]), s['bold'])] for r in info_rows],
        colWidths=[5 * cm, 12 * cm],
    )
    user_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(user_table)
    story.append(Spacer(1, 0.6 * cm))

    # Quick summary stats
    w = data['workouts']['stats']
    n = data['nutrition']['stats']
    b = data['calorie_balance']
    p = data['progress']

    wt_change = p['weight_change']
    wt_color = ACCENT if (wt_change is not None and wt_change <= 0) else DANGER

    cards = Table(
        [[
            _stat_card('Workouts', w['total_sessions']),
            _stat_card('Minutes Active', w['total_minutes']),
            _stat_card('Calories Burned', int(w['total_calories_burned']), 'kcal', ACCENT),
            _stat_card('Avg Daily Food', int(n['avg_daily_calories']), 'kcal', WARNING),
        ]],
        colWidths=[4.3 * cm] * 4,
        hAlign='CENTER',
    )
    story.append(cards)
    story.append(Spacer(1, 0.4 * cm))

    cards2 = Table(
        [[
            _stat_card('Net Calories', int(b['net']), 'kcal'),
            _stat_card('Weight Change', f"{'+' if (wt_change or 0) > 0 else ''}{wt_change or '—'}", 'kg', wt_color),
            _stat_card('Days Logged Food', n['days_with_food_log']),
            _stat_card('Protein Consumed', int(n['total_protein']), 'g', ACCENT),
        ]],
        colWidths=[4.3 * cm] * 4,
        hAlign='CENTER',
    )
    story.append(cards2)


def _workout_section(story, data: dict, s: dict):
    story.append(PageBreak())
    story += _section_header('Workout Analysis', s)

    w = data['workouts']
    stats = w['stats']
    by_type = w['by_type']

    summary_data = [
        [Paragraph('Metric', s['bold']), Paragraph('Value', s['bold'])],
        ['Total Sessions', str(stats['total_sessions'])],
        ['Total Duration', f"{stats['total_minutes']} min  ({round(stats['total_minutes']/60, 1)} hrs)"],
        ['Total Calories Burned', f"{stats['total_calories_burned']} kcal"],
        ['Avg Session Duration', f"{round(stats['total_minutes'] / stats['total_sessions'], 1) if stats['total_sessions'] else 0} min"],
    ]
    _styled_table(story, summary_data, [8 * cm, 9 * cm])
    story.append(Spacer(1, 0.4 * cm))

    if by_type:
        story += _section_header('Breakdown by Type', s)
        type_data = [
            [Paragraph(h, s['bold']) for h in ['Type', 'Sessions', 'Duration (min)', 'Calories']],
        ]
        for t, v in by_type.items():
            type_data.append([t.title(), str(v['sessions']), str(v['minutes']), f"{round(v['calories'], 1)} kcal"])
        _styled_table(story, type_data, [5 * cm, 3.5 * cm, 4.5 * cm, 4 * cm])
        story.append(Spacer(1, 0.4 * cm))

    if w['sessions']:
        story += _section_header('Session Log', s)
        session_data = [
            [Paragraph(h, s['bold']) for h in ['Date', 'Exercise', 'Type', 'Duration', 'Cal. Burned']],
        ]
        for ses in w['sessions']:
            session_data.append([
                ses['date'], ses['workout'], ses['type'].title(),
                f"{ses['duration_min']} min", f"{ses['calories_burned']} kcal",
            ])
        _styled_table(story, session_data, [3 * cm, 5 * cm, 3 * cm, 3 * cm, 3 * cm])


def _nutrition_section(story, data: dict, s: dict):
    story.append(PageBreak())
    story += _section_header('Nutrition & Calorie Tracking', s)

    n = data['nutrition']['stats']
    b = data['calorie_balance']

    summary_data = [
        [Paragraph('Metric', s['bold']), Paragraph('Value', s['bold'])],
        ['Total Calories Consumed', f"{n['total_calories_in']} kcal"],
        ['Avg Daily Calories', f"{n['avg_daily_calories']} kcal"],
        ['Total Protein', f"{n['total_protein']} g"],
        ['Total Carbohydrates', f"{n['total_carbs']} g"],
        ['Total Fat', f"{n['total_fat']} g"],
        ['Days with Food Logs', str(n['days_with_food_log'])],
        ['Total Calories Burned', f"{b['total_burned']} kcal"],
        ['Net Calorie Balance', f"{b['net']} kcal ({'surplus' if b['net'] > 0 else 'deficit'})"],
    ]
    _styled_table(story, summary_data, [9 * cm, 8 * cm])
    story.append(Spacer(1, 0.4 * cm))

    by_day = data['nutrition']['by_day']
    if by_day:
        story += _section_header('Daily Food Log', s)
        for day, day_data in sorted(by_day.items()):
            story.append(Paragraph(f"📅  {day}  —  {round(day_data['total_calories'], 1)} kcal total", s['bold']))
            items_data = [
                [Paragraph(h, s['muted']) for h in ['Food', 'Meal', 'Quantity', 'Calories']],
            ]
            for item in day_data['items']:
                items_data.append([
                    item['name'], item['meal_type'].title(),
                    item.get('quantity', '—'), f"{item['calories']} kcal",
                ])
            _styled_table(story, items_data, [6 * cm, 3 * cm, 4 * cm, 4 * cm])
            story.append(Spacer(1, 0.3 * cm))


def _progress_section(story, data: dict, s: dict):
    story.append(PageBreak())
    story += _section_header('Body Progress', s)

    p = data['progress']
    if not p['entries']:
        story.append(Paragraph('No progress entries recorded for this period.', s['muted']))
        return

    wc = p['weight_change']
    wc_text = f"{'+' if (wc or 0) > 0 else ''}{wc} kg" if wc is not None else '—'
    summary_data = [
        [Paragraph('Metric', s['bold']), Paragraph('Value', s['bold'])],
        ['Starting Weight', f"{p['start_weight']} kg" if p['start_weight'] else '—'],
        ['Ending Weight', f"{p['end_weight']} kg" if p['end_weight'] else '—'],
        ['Net Weight Change', wc_text],
    ]
    _styled_table(story, summary_data, [8 * cm, 9 * cm])
    story.append(Spacer(1, 0.4 * cm))

    story += _section_header('Progress Log', s)
    log_data = [[Paragraph(h, s['bold']) for h in ['Date', 'Weight (kg)', 'Notes']]]
    for e in p['entries']:
        log_data.append([e['date'], str(e['weight_kg']) if e['weight_kg'] else '—', e.get('note', '') or '—'])
    _styled_table(story, log_data, [4 * cm, 4 * cm, 9 * cm])


def _ai_section(story, ai_summary: str, s: dict):
    story.append(PageBreak())
    story += _section_header('AI Coach Recommendations', s)

    if not ai_summary:
        story.append(Paragraph('AI analysis not available for this report.', s['muted']))
        return

    # Parse sections from Gemini output
    lines = ai_summary.split('\n')
    for line in lines:
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 0.15 * cm))
        elif stripped.startswith('**') and stripped.endswith('**'):
            story.append(Paragraph(stripped.strip('*'), s['ai_heading']))
        elif stripped.startswith('- ') or stripped.startswith('• '):
            story.append(Paragraph(f"&bull;&nbsp;&nbsp;{stripped[2:]}", s['ai_body']))
        elif stripped.startswith('*') and not stripped.endswith('*'):
            story.append(Paragraph(f"&bull;&nbsp;&nbsp;{stripped[1:].strip()}", s['ai_body']))
        else:
            story.append(Paragraph(stripped, s['ai_body']))


def _styled_table(story, data, col_widths):
    t = Table(data, colWidths=col_widths)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, CARD_BG]),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    t.setStyle(style)
    story.append(t)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(2 * cm, 1.2 * cm, 'FitnessAI — Confidential Report')
    canvas.drawRightString(19 * cm, 1.2 * cm, f'Page {doc.page}')
    canvas.restoreState()


def generate_pdf(report_data: dict, ai_summary: str, period: str,
                 period_start: str, period_end: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title=f"FitnessAI {period.title()} Report",
        author='FitnessAI',
    )

    s = _styles()
    story = []

    _cover_page(story, report_data, period, period_start, period_end, s)
    _workout_section(story, report_data, s)
    _nutrition_section(story, report_data, s)
    _progress_section(story, report_data, s)
    _ai_section(story, ai_summary, s)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
