# Ralph Quick Start - KIE v3

## ✅ Everything is Ready

All files configured and ready to go!

## Run Ralph (3 Steps)

### 1. Open Claude Code Desktop App
(Not CLI, not terminal - the desktop application)

### 2. Navigate to Project
```
cd ~/Projects/kie-v3
```

### 3. Run Ralph Command
```
/ralph-loop "Work through @fix_plan.md tasks autonomously. Follow PROMPT.md instructions. Write comprehensive tests for all chart builders. Run tests after writing. Mark tasks [x] when complete. Output <promise>COMPLETE</promise> when all 35 tasks done and tests passing." --max-iterations 50 --completion-promise "COMPLETE"
```

## That's It!

Ralph will:
- ✅ Write tests for 7 chart builders
- ✅ Test intelligence systems
- ✅ Test validation systems
- ✅ Run all tests
- ✅ Mark tasks complete
- ✅ Continue until done

## Monitor Progress

```bash
# Watch tasks complete
watch -n 10 "cat ~/Projects/kie-v3/@fix_plan.md | grep -c '\[x\]'"

# See new test files
ls -lt ~/Projects/kie-v3/tests/*.py | head -10
```

## Expected Duration

- 35 tasks to complete
- ~2-3 minutes per task
- **Total: 70-105 minutes (1-2 hours)**

## Cost

- ~$0.50-0.60 total (uses your CC subscription)
- Much cheaper than expected!

## Files Created

Ralph will create:
- `tests/test_bar_chart_builder.py` (~45 tests)
- `tests/test_line_chart_builder.py` (~40 tests)
- `tests/test_pie_chart_builder.py` (~35 tests)
- `tests/test_area_chart_builder.py` (~35 tests)
- `tests/test_scatter_chart_builder.py` (~30 tests)
- `tests/test_waterfall_chart_builder.py` (~25 tests)
- `tests/test_combo_chart_builder.py` (~30 tests)
- `tests/test_chart_factory.py` (~20 tests)
- `tests/test_data_loader.py` (~25 tests)
- `tests/test_output_validator.py` (~30 tests)
- `tests/test_kds_colors.py` (~15 tests)

**Total: ~330 new tests protecting your core functionality!**

---

**Ready?** Open Claude Code desktop app and paste the `/ralph-loop` command above! 🚀
