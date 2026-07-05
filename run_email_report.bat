@echo off
REM Bluestock Fintech - Mutual Fund Analytics Capstone
REM B1: Cron Job (Windows Task Scheduler trigger script)
REM
REM This batch file is what Task Scheduler runs daily.
REM It changes into the project folder, runs the email report script,
REM and logs output with a timestamp for auditing.

cd /d "C:\Users\KIIT\Desktop\MutualFund-Analytics\mf-analytics\mf-analytics"

echo ============================================== >> logs\email_report_log.txt
echo Run started: %date% %time% >> logs\email_report_log.txt
python email_report.py >> logs\email_report_log.txt 2>&1
echo Run finished: %date% %time% >> logs\email_report_log.txt
echo ============================================== >> logs\email_report_log.txt
