identify vulnerabilities and report findings, but don't modify files or attempt fixes. create an .md file for report. 



## Final Security Decision

After completing the security review:

1. Report all findings with their severity, confidence, affected file,
   location, vulnerability, impact, and recommended mitigation.

2. Determine the overall security status:
   - FAIL: At least one HIGH or CRITICAL finding exists.
   - PASS: No HIGH or CRITICAL findings exist.

3. At the very end of the report, print exactly one of these lines:

   SECURITY_REVIEW_STATUS: PASS

   SECURITY_REVIEW_STATUS: FAIL

4. Do not ask the user what to do next.
5. Do not modify any files.
6. Do not attempt to fix vulnerabilities.
7. Do not commit or push changes.