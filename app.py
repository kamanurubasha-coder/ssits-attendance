import os
import time
import webbrowser
from datetime import datetime
import pandas as pd
import pyautogui
import pyperclip
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# ----------------------------------------------------
# 1. SETTINGS, DIRECTORIES & CONTACTS
# ----------------------------------------------------
st.set_page_config(
    page_title="SSITS Attendance Portal",
    page_icon="🎓",
    layout="wide"
)

DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
REPORTS_DIR = os.path.join(DESKTOP_PATH, "SSITS_Attendance_Reports")
LOG_FILE = os.path.join(DESKTOP_PATH, "SSITS_Attendance_Master_Log.csv")

if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

CSV_BASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT-MgCBYAMCM_45VMeiX9OZaA07EtYEAy3ilMfun2BzSRQKLCmS20_rCVRJGMz9w8Z1hZIC7-dLWtaf/pub?output=csv"

# Authority Contacts
PRINCIPAL_PHONE = "9515139866"
HOD_PHONES = {
    "ECE": "9515139866",
    "EEE": "9515139866",
    "CSE": "9515139866",
    "MECH": "9515139866",
    "CIVIL": "9515139866",
}

screen_w, screen_h = pyautogui.size()

# ----------------------------------------------------
# 2. WHATSAPP DISPATCH ENGINE
# ----------------------------------------------------
def send_whatsapp_message(phone, message_text):
    try:
        pyperclip.copy(message_text)
        webbrowser.open(f"whatsapp://send?phone={phone}")
        time.sleep(4)
        
        pyautogui.click(screen_w // 2, screen_h // 2)
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.8)
        pyautogui.press('enter')
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(2)
        return True
    except Exception as e:
        st.error(f"WhatsApp Dispatch Error ({phone}): {e}")
        return False

# ----------------------------------------------------
# 3. PDF REPORT ENGINE
# ----------------------------------------------------
def create_pdf_report(filepath, title_text, dept_name, rows, summary=""):
    try:
        doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=12, leading=15, alignment=1, textColor=colors.HexColor('#1A237E'))
        sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=9, leading=12, alignment=1, textColor=colors.HexColor('#333333'))

        elements.append(Paragraph("<b>SRI SAI INSTITUTE OF TECHNOLOGY AND SCIENCE</b>", title_style))
        elements.append(Paragraph(f"DEPARTMENT OF {dept_name}", sub_style))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(f"<b>{title_text}</b>", title_style))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}", sub_style))
        elements.append(Spacer(1, 12))

        headers = ["Roll No", "Student Name", "Parent Name", "Phone", "Status"]
        if not rows:
            rows = [["-", "No Absentees / Full Attendance", "-", "-", "NIL"]]

        table_data = [headers] + rows
        col_widths = [65, 140, 110, 100, 100]

        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#283593')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ]))
        elements.append(table)

        if summary:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"<b>{summary}</b>", sub_style))

        doc.build(elements)
        return True
    except Exception as e:
        st.error(f"PDF Generation Error: {e}")
        return False

# ----------------------------------------------------
# 4. MASTER LOGGING
# ----------------------------------------------------
def log_daily_attendance(records):
    try:
        log_df = pd.DataFrame(records)
        if not os.path.exists(LOG_FILE):
            log_df.to_csv(LOG_FILE, index=False)
        else:
            log_df.to_csv(LOG_FILE, mode='a', header=False, index=False)
    except Exception as e:
        st.error(f"Master Log Error: {e}")

# ----------------------------------------------------
# 5. UI INTERFACE
# ----------------------------------------------------
st.title("SRI SAI INSTITUTE OF TECHNOLOGY AND SCIENCE")
st.subheader("Official Attendance & WhatsApp Alert Portal")

col1, col2, col3 = st.columns(3)
with col1:
    dept = st.selectbox("Select Department:", ["ECE", "EEE", "CSE", "MECH", "CIVIL"])
with col2:
    session = st.radio("Select Session:", ["Morning", "Afternoon"], horizontal=True)
with col3:
    today_str = datetime.now().strftime("%d-%m-%Y")
    st.write(f"**Date:** {today_str}")

st.divider()

# Load Students from Google Sheet
@st.cache_data(ttl=5)
def load_dept_students(selected_dept):
    url = f"{CSV_BASE_URL}&sheet={selected_dept}"
    try:
        df_raw = pd.read_csv(url, header=None, dtype=str)
        students = []
        for idx in range(3, len(df_raw)):
            row = df_raw.iloc[idx]
            parent = str(row[0]).strip()
            name = str(row[1]).strip()
            roll = str(row[2]).strip().replace('.0', '')
            digits = ''.join(filter(str.isdigit, str(row[3])))
            
            if digits.startswith("91") and len(digits) == 12:
                phone_10 = digits[2:]
            elif len(digits) >= 10:
                phone_10 = digits[:10]
            else:
                phone_10 = ""
            phone = "91" + phone_10 if phone_10 else ""

            if name and name.lower() != "nan":
                students.append({
                    "Roll No": roll,
                    "Student Name": name,
                    "Parent Name": parent,
                    "Phone": phone,
                    "Absent": False
                })
        return pd.DataFrame(students)
    except Exception as e:
        return pd.DataFrame()

students_df = load_dept_students(dept)

if not students_df.empty:
    st.write(f"### {dept} Department Students List")
    st.caption("Check the box next to the student's name to mark as absent:")

    edited_df = st.data_editor(
        students_df,
        column_config={
            "Absent": st.column_config.CheckboxColumn("Mark Absent", default=False)
        },
        disabled=["Roll No", "Student Name", "Parent Name", "Phone"],
        hide_index=True,
        use_container_width=True
    )

    # ----------------------------------------------------
    # 6. TRIGGER & DISPATCH ACTION
    # ----------------------------------------------------
    if st.button("Submit Attendance & Send WhatsApp Alerts", type="primary"):
        absentees = edited_df[edited_df["Absent"] == True]
        all_students = edited_df.to_dict('records')
        
        pdf_data = []
        absent_rolls = []
        daily_records = []
        sent_total = 0

        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, student in enumerate(all_students):
            roll = student["Roll No"]
            s_name = student["Student Name"]
            parent = student["Parent Name"]
            phone = student["Phone"]
            is_absent = student["Absent"]

            status_for_log = "A" if is_absent else "P"

            daily_records.append({
                "Date": today_str,
                "Department": dept,
                "Session": session.upper(),
                "Roll No": roll,
                "Student Name": s_name,
                "Status": status_for_log
            })

            if is_absent:
                absent_rolls.append(roll)
                status_label = "ABSENT" if session == "Morning" else "HALF DAY BUNK"
                pdf_data.append([roll, s_name, parent, phone, status_label])

                if session == "Morning":
                    msg = (
                        f"-- OFFICIAL ATTENDANCE ALERT --\n"
                        f"SRI SAI INSTITUTE OF TECHNOLOGY & SCIENCE\n"
                        f"Department of {dept}\n\n"
                        f"Date: {today_str} (Morning Session)\n"
                        f"Dear Mr./Mrs. {parent},\n\n"
                        f"This is to inform you that your ward {s_name} (Roll No: {roll}) is ABSENT from college today.\n\n"
                        f"తేదీ: {today_str} (ఉదయం పూట)\n"
                        f"గౌరవనీయులైన {parent} గారికి,\n"
                        f"మీ పిల్లలు {s_name} (రోల్ నం: {roll}) ఈరోజు కళాశాలకు హాజరు కాలేదు (ABSENT). దయచేసి గమనించగలరు.\n\n"
                        f"- HOD, {dept} Department, SSITS"
                    )
                else:
                    msg = (
                        f"-- OFFICIAL ATTENDANCE ALERT --\n"
                        f"SRI SAI INSTITUTE OF TECHNOLOGY & SCIENCE\n"
                        f"Department of {dept}\n\n"
                        f"Date: {today_str} (Afternoon Session)\n"
                        f"Dear Mr./Mrs. {parent},\n\n"
                        f"This is to inform you that your ward {s_name} (Roll No: {roll}) attended the morning session but is ABSENT for the afternoon classes (HALF DAY BUNK).\n\n"
                        f"తేదీ: {today_str} (మధ్యాహ్నం పూట)\n"
                        f"గౌరవనీయులైన {parent} గారికి,\n"
                        f"మీ పిల్లలు {s_name} (రోల్ నం: {roll}) ఉదయం కాలేజీకి వచ్చి మధ్యాహ్నం వెళ్లిపోయారు (HALF DAY BUNK). దయచేసి గమనించగలరు.\n\n"
                        f"- HOD, {dept} Department, SSITS"
                    )

                if phone:
                    status_text.text(f"Sending WhatsApp notification to {s_name} (Roll: {roll})...")
                    send_whatsapp_message(phone, msg)
                    sent_total += 1

            progress_bar.progress((idx + 1) / len(all_students))

        # Save to Master Log
        log_daily_attendance(daily_records)

        # Generate & Save Daily PDF Report
        pdf_filename = f"{dept}_{session}_Report_{today_str}.pdf"
        out_pdf = os.path.join(REPORTS_DIR, pdf_filename)
        report_title = f"{session.upper()} ATTENDANCE REPORT ({today_str})"
        create_pdf_report(out_pdf, report_title, dept, pdf_data, f"Total Absentees: {len(pdf_data)} | Alerts Dispatched: {sent_total}")

        # Send Official Summary to HOD & Principal
        rolls_display = ", ".join(absent_rolls) if absent_rolls else "NIL"
        summary_msg = (
            f"-- SSITS OFFICIAL ATTENDANCE REPORT --\n"
            f"DEPARTMENT: {dept}\n"
            f"Session: {session.upper()} ({today_str})\n"
            f"--------------------------------------------------\n"
            f"Total Absentees: {len(pdf_data)}\n"
            f"Absent Roll Numbers:\n{rolls_display}\n"
            f"--------------------------------------------------\n"
            f"Official PDF Report generated and archived on server.\n"
            f"SSITS Automated System"
        )

        dept_hod = HOD_PHONES.get(dept)
        if dept_hod:
            status_text.text(f"Dispatching summary report to {dept} HOD...")
            send_whatsapp_message(dept_hod, summary_msg)

        if PRINCIPAL_PHONE and (PRINCIPAL_PHONE != dept_hod):
            status_text.text("Dispatching summary report to Principal...")
            send_whatsapp_message(PRINCIPAL_PHONE, summary_msg)

        status_text.empty()
        progress_bar.empty()

        st.success(f"Execution Completed Successfully! Total Absentees: {len(pdf_data)} | WhatsApp Alerts Sent: {sent_total}")
        st.info(f"Official PDF Report archived in Desktop folder: SSITS_Attendance_Reports")

else:
    st.warning("No student records found. Please verify network connection or Google Sheet publication settings.")