#!/bin/bash

# Activate the virtual environment (optional now)
source /home/pi/test_project/venv/bin/activate

# Get current timestamp for the file name
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")  # Include seconds for uniqueness
DATE=$(date +"%Y-%m-%d")
TIME=$(date +"%H:%M:%S")
RESULT_FILE="/home/pi/test_project/test_results/results.csv"
METRIC_FILE="/home/pi/test_project/test_results/metrics_$TIMESTAMP.prom"

# Create test_results directory if it doesn't exist
mkdir -p /home/pi/test_project/test_results

# Check if the results directory is writable
if [ ! -w /home/pi/test_project/test_results/ ]; then
    echo "No write permission for the results directory."
    exit 1
fi

cd /home/pi/test_project

# Run unittest explicitly on the test_api.py file and capture output
TEST_OUTPUT=$(python3 -m unittest test_api 2>&1)

# Debug: Output the raw test result for inspection
echo "Raw Test Output:"
echo "$TEST_OUTPUT"

# Parse the unittest output to count passed and failed tests
FAIL_COUNT=$(echo "$TEST_OUTPUT" | grep -o 'FAIL' | wc -l)

# Extract the total number of tests run from the output
TOTAL_TESTS=$(echo "$TEST_OUTPUT" | grep -o 'Ran [0-9]* tests' | grep -o '[0-9]*')

# Calculate the number of passed tests
PASS_COUNT=$((TOTAL_TESTS - FAIL_COUNT))

# Extract the failed test cases from the output
FAILED_TESTS=$(echo "$TEST_OUTPUT" | grep 'FAIL' | awk -F ' ' '{print $2}' | paste -sd ", ")

# Determine the status
if [ "$FAIL_COUNT" -eq 0 ]; then
    STATUS="Passed"
    FAILED_TEST_CASES="No failed tests"
else
    STATUS="Failed"
    FAILED_TEST_CASES=$FAILED_TESTS
fi

# Check if the CSV file exists, if not, create it and add headers
if [ ! -f "$RESULT_FILE" ]; then
    echo "Date,Time,Total Tests,Passed,Failed,Status,Failed Test Cases" > "$RESULT_FILE"
fi

# Append the results to the CSV file
echo "$DATE,$TIME,$TOTAL_TESTS,$PASS_COUNT,$FAIL_COUNT,$STATUS,$FAILED_TEST_CASES" >> "$RESULT_FILE"

# Generate the metrics file for Prometheus-style monitoring
cat <<EOF > "$METRIC_FILE"
# HELP unit_test_passed Total passed unit tests
# TYPE unit_test_passed gauge
unit_test_passed $PASS_COUNT

# HELP unit_test_failed Total failed unit tests
# TYPE unit_test_failed gauge
unit_test_failed $FAIL_COUNT

# HELP failed_tests Names of the failed test cases
# TYPE failed_tests gauge
failed_tests "$FAILED_TEST_CASES"
EOF

# Display the results to console (optional)
echo "Test results saved to: $RESULT_FILE"
echo "Metrics saved to: $METRIC_FILE"
echo "Total Tests: $TOTAL_TESTS"
echo "Total Passed Tests: $PASS_COUNT"
echo "Total Failed Tests: $FAIL_COUNT"
echo "Failed Test Cases: $FAILED_TEST_CASES"

#########################################
# SLACK NOTIFICATION SECTION
#########################################

SLACK_WEBHOOK_URL="https://hooks.slack.com/services/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"  # Replace with your actual Slack webhook URL

# Escape quotes and backslashes for JSON
SUMMARY=$(echo "$TEST_OUTPUT" | tail -n 10 | sed 's/\\/\\\\/g' | sed 's/"/\\"/g')

if [ "$STATUS" = "Passed" ]; then
    SLACK_MESSAGE="✅ *Test Run Passed* at $DATE $TIME\nTotal: $TOTAL_TESTS, Passed: $PASS_COUNT"
else
    SLACK_MESSAGE="❌ *Test Run FAILED* at $DATE $TIME\nTotal: $TOTAL_TESTS, Failed: $FAIL_COUNT\n*Failed Cases:* $FAILED_TEST_CASES\n\`\`\`$SUMMARY\`\`\`"
fi

curl -X POST -H 'Content-type: application/json' \
  --data "{
    \"text\": \"$SLACK_MESSAGE\"
  }" $SLACK_WEBHOOK_URL

#########################################

# Fetch interval from timer file and compute next run time
TIMER_FILE="/etc/systemd/system/unit_test.timer"
INTERVAL=$(grep -oP 'OnUnitActiveSec=\K[^\n]+' "$TIMER_FILE" | sed 's/[^0-9]*//g')  # Extracting the interval (12 hours) in seconds
CURRENT_TIME=$(date +"%Y-%m-%d %H:%M:%S")
NEXT_TIME=$(date -d "+${INTERVAL} seconds" +"%Y-%m-%d %H:%M:%S")

# Save the last run and next scheduled time to JSON file for the UI
echo "{\"last_run\": \"$CURRENT_TIME\", \"next_run\": \"$NEXT_TIME\"}" > /home/pi/test_project/ui/static/test_schedule.json


