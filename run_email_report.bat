@echo off
REM Bluestock Fintech - Mutual Fund Analytics Capstone
REM B5: HTML Email Report - weekly cron job trigger script
REM
REM Uses Python's full path since Task Scheduler often can't resolve
REM "python" via PATH the way an interactive terminal can.

cd /d "C:\Users\KIIT\Desktop\MutualFund-Analytics\mf-analytics\mf-analytics"

echo ============================================== >> logs\email_report_log.txt
echo Run started: %date% %time% >> logs\email_report_log.txt
"C:\Users\KIIT\AppData\Local\Python\pythoncore-3.14-64\python.exe" email_report.py >> logs\email_report_log.txt 2>&1
echo Run finished: %date% %time% >> logs\email_report_log.txt
echo ============================================== >> logs\email_report_log.txt
