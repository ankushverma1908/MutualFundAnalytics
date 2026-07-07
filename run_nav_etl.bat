@echo off
REM Bluestock Fintech - Mutual Fund Analytics Capstone
REM B1: ETL Cron Job - fetches live NAV from mfapi.in and loads into fact_nav
REM Scheduled: weekdays at 8:00 PM (per assignment brief)
REM
REM Uses Python's full path since Task Scheduler often can't resolve
REM "python" via PATH the way an interactive terminal can.

cd /d "C:\Users\KIIT\Desktop\MutualFund-Analytics\mf-analytics\mf-analytics"

echo ============================================== >> logs\nav_etl_log.txt
echo Run started: %date% %time% >> logs\nav_etl_log.txt
"C:\Users\KIIT\AppData\Local\Python\pythoncore-3.14-64\python.exe" live_nav_fetch.py >> logs\nav_etl_log.txt 2>&1
echo Run finished: %date% %time% >> logs\nav_etl_log.txt
echo ============================================== >> logs\nav_etl_log.txt
