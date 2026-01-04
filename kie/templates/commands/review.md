# Review Command

You are running the KIE review process. Validate brand compliance of all outputs.

## Review Process

1. **Scan outputs folder**
   - List all files in `outputs/` and `exports/`

2. **Check each deliverable against brand rules**

### Brand Compliance Checklist

For each file, verify:

**Color Rules:**
- [ ] Primary purple (#7823DC) used appropriately
- [ ] NO green colors anywhere (forbidden)
- [ ] Dark background (#1E1E1E) where applicable
- [ ] White (#FFFFFF) or light purple (#9B4DCA) text on dark - NEVER primary purple
- [ ] Proper data colors from palette

**Chart Rules (React/Recharts):**
- [ ] No gridlines visible
- [ ] Data labels positioned OUTSIDE bars/slices
- [ ] Arial/Inter font used
- [ ] Dark background (#1E1E1E)
- [ ] White axis labels and text

**PowerPoint Rules (if .pptx):**
- [ ] Dark slide backgrounds (#1E1E1E)
- [ ] White text on dark slides
- [ ] No emojis
- [ ] Kearney purple for highlights only
- [ ] Clean, minimal design

**General:**
- [ ] No emojis anywhere
- [ ] WCAG AA contrast met
- [ ] Professional tone
- [ ] Consistent branding

## Review Report

For each file, report:
```
outputs/chart1.png
✓ Dark background
✓ No gridlines
✗ Data labels inside bars (MUST be outside)
✗ Green color detected at (#00FF00) - FORBIDDEN

Status: FAIL - 2 issues
```

## Remediation

If issues found:
1. List all problems clearly
2. Offer to fix automatically
3. Re-run review after fixes

## Completion

```
Review complete!
- X files passed
- Y files failed
- Total issues: Z

Ready to export? All files must pass review first.
```
