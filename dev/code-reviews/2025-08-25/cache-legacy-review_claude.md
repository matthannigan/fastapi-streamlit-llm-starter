# Taskplan

Phase 1: Address Minor Legacy Issues First (1-2 hours)

From cache-legacy-review_claude2.md:
1. Parameter naming consistency in backend/app/api/v1/deps.py (5 minutes)
2. Update documentation examples that still use legacy methods (30-60 minutes)
3. Update test mocks to use standard interface (15-30 minutes)
4. Clean up legacy environment variable references (15-30 minutes)

Phase 2: Then Execute Major Elimination (8-10 hours)

Follow the taskplan deliverables 1-4

Strategic Benefits of This Approach:

🎯 Reduces Surface Area

- Eliminates all the "small" legacy references before major refactoring
- Prevents having to update documentation examples twice
- Cleans up test patterns before major test updates

🔍 Makes Impact Clear

- After minor cleanup, the cache method elimination becomes the ONLY remaining legacy issue
- Easier to validate that elimination is complete
- Cleaner diff showing just the architectural changes

⚡ Faster Validation

- Minor issues can be addressed quickly with immediate validation
- Major refactoring won't be cluttered with trivial documentation fixes
- Easier to test each change individually

🛡️ Risk Mitigation

- Low-risk documentation/naming changes first
- High-risk architectural changes on a cleaner codebase
- If major refactoring encounters issues, minor improvements are already locked in

Updated Recommendation:

1. Start with the minor issues from the legacy review (quick wins)
2. Then proceed with Deliverable 1-4 of the elimination taskplan
3. Final validation will be cleaner with only architectural changes to verify

This approach follows the principle of "clean up the noise before the signal" - making the major architectural changes more focused and easier to validate.

### backend/examples/ directory files
Example files that demonstrate usage patterns. These should be updated after the main codebase is cleaned:
- `examples/cache_configuration_examples.py`
- `examples/cache/*.py` - All cache example files

**Recommendation:** **UPDATE AFTER MAIN CLEANUP** - These serve as documentation and should reflect the final architecture.

### Files That Should NOT Be Deleted
- `backend/app/infrastructure/cache/compatibility.py` - **Still exists and may serve migration purposes**
- All other cache infrastructure files - **Modern, production-ready implementations**

