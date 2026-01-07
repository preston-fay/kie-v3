# Ralph Setup for KIE v3 - Ready to Launch! 🚀

## What Ralph Will Do

Ralph will work through a **hybrid test coverage + API implementation plan** with 4 phases:

### Phase 1: Test Coverage Blitz (12-15 hours)
✅ **Zero risk** - Testing existing stable code
- Test all 7 chart builders (bar, line, pie, area, scatter, waterfall, combo)
- Test ChartFactory auto-detection
- Test DataLoader 4-tier semantic intelligence
- Test OutputValidator (KDS compliance)
- Test KDS color system

### Phase 2: API Completion (6-8 hours)
📝 **Clear scope** - Implement marked TODOs
- Implement 6 FastAPI routes for projects and charts
- Add comprehensive API tests
- Complete the FastAPI backend

### Phase 3: Additional Coverage (8-10 hours) - Optional
- Test EDA engine, table export
- Test insights and workflow orchestration

### Phase 4: Nice-to-Haves (4-6 hours) - Optional
- Documentation improvements
- Type hints and docstrings
- Example scripts

## Launch Ralph

### Quick Start (Recommended Settings)
```bash
cd ~/Projects/kie-v3
export PATH="$HOME/.local/bin:$PATH"
ralph --monitor --timeout 60 --calls 75 --verbose
```

### For Overnight Run (Full Phase 1)
```bash
ralph --monitor --timeout 120 --calls 100 --verbose
```

### For Quick Testing (Single task)
```bash
ralph --timeout 30 --calls 50 --verbose
```

## What to Expect

### First Loop (Test BarChartBuilder)
Ralph will:
1. Search the codebase to find BarChartBuilder at `kie/charts/builders/bar.py`
2. Study existing test patterns in `tests/`
3. Write comprehensive tests for BarChartBuilder
4. Run tests: `pytest tests/test_chart_bar.py -v`
5. Verify integration: `pytest tests/test_v3_integration.py`
6. Mark task [x] in `.ralph/fix_plan.md`
7. Report status and move to next task

### Progress Tracking
- **Live monitoring**: Detach with `Ctrl+B` then `D`, reattach with `tmux attach -t ralph`
- **Check status**: `ralph --status`
- **View task list**: `cat .ralph/fix_plan.md`
- **View logs**: `tail -f logs/ralph_*.log`

## Files Created

```
kie-v3/
├── .ralph/
│   ├── PROMPT.md       # Ralph's instruction manual (KIE-specific)
│   └── fix_plan.md     # Prioritized task list (4 phases)
└── RALPH_SETUP.md      # This file
```

## Success Criteria

### Phase 1 Complete When:
- ✅ 50+ new tests written
- ✅ All chart builders have test coverage
- ✅ Validation and intelligence systems tested
- ✅ All tests passing: `pytest`
- ✅ Integration test passing: `pytest tests/test_v3_integration.py`

### Phase 2 Complete When:
- ✅ 6 API routes implemented
- ✅ API tests written and passing
- ✅ FastAPI backend fully functional

## Monitoring Ralph

### Real-Time Monitoring
```bash
# Start with monitoring
ralph --monitor --timeout 60 --calls 75 --verbose

# Detach: Ctrl+B then D
# Do other work...
# Reattach: tmux attach -t ralph
```

### Check Progress
```bash
# View what Ralph has completed
cat .ralph/fix_plan.md | grep '\[x\]'

# View current status
ralph --status

# View recent activity
tail -20 logs/ralph_$(date +%Y%m%d)_*.log
```

### Circuit Breaker
Ralph will auto-stop if:
- Same error occurs 5+ times (circuit opens)
- Test-only loops 3+ times with no implementation
- Completion signal: `EXIT_SIGNAL: true`

## Cost Estimate

**Phase 1** (12-15 hours):
- Conservative: 75 calls/hour × 12 hours = 900 API calls
- Generous: 100 calls/hour × 15 hours = 1500 API calls
- Cost on Max plan: ~$30-50 depending on context size

**Phase 2** (6-8 hours):
- Conservative: 75 calls/hour × 6 hours = 450 API calls
- Generous: 100 calls/hour × 8 hours = 800 API calls
- Cost: ~$15-30

**Total for Phases 1+2**: ~$45-80

## Safety Features

### What Ralph WON'T Do
❌ Break existing functionality (only adds tests)
❌ Use green colors (KDS violation detection)
❌ Skip tests (required for every task)
❌ Add new dependencies (blocked)
❌ Refactor unrelated code (out of scope)

### What Ralph WILL Do
✅ Search codebase before implementing
✅ Follow existing patterns
✅ Write comprehensive tests
✅ Run integration tests after changes
✅ Report detailed status
✅ Stop when blocked or complete

## Troubleshooting

### "ralph: command not found"
```bash
export PATH="$HOME/.local/bin:$PATH"
# Or restart terminal
```

### Ralph keeps running same tests
Circuit breaker will detect and exit after 3 loops.

### Ralph is blocked
Check status:
```bash
ralph --status
cat .ralph/fix_plan.md  # See what's marked [x]
```

### Reset circuit breaker
```bash
ralph --reset-circuit
```

## Next Steps

1. **Review the task list**: `cat .ralph/fix_plan.md`
2. **Adjust if needed**: Edit `.ralph/fix_plan.md` to prioritize differently
3. **Launch Ralph**: `ralph --monitor --timeout 60 --calls 75 --verbose`
4. **Detach and monitor**: `Ctrl+B` then `D`, check back periodically
5. **Review results**: Check test coverage and completed tasks

## Expected Outcomes

After Phase 1:
- **50+ new test files** protecting core functionality
- **80%+ test coverage** on chart builders and validation
- **Zero untested chart builders** (currently 7 have NO tests)
- **Protected intelligence** (DataLoader semantic scoring tested)
- **KDS compliance verified** (OutputValidator tested)

After Phase 2:
- **Complete FastAPI backend** (6 routes implemented)
- **API fully tested** (error handling, edge cases)
- **Ready for frontend integration**

---

**Ready to launch?** Run: `ralph --monitor --timeout 60 --calls 75 --verbose`

**Questions?** Check `~/.ralph/RALPH_SETUP_GUIDE.md` for full Ralph documentation.
