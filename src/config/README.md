# Oracle I Ching Configuration

This directory contains configuration modules that centralize settings used throughout the application.

## Quota Settings

The quota settings are centralized in `quotas.py`. These settings control how many readings users can request based on their membership type.

### Environment Variables

All quota settings can be overridden using environment variables:

| Environment Variable | Description | Default |
| --- | --- | --- |
| `FREE_PLAN_QUOTA` | Number of queries allowed for free tier users | 10 |
| `PREMIUM_PLAN_QUOTA` | Number of queries allowed for premium tier users | 50 |
| `LOW_QUOTA_THRESHOLD` | Threshold at which to show "running low" warnings | 3 |

### Important Notes

1. The `FREE_PLAN_QUOTA` value is now directly imported by `scripts/generate_supabase_setup.py` to generate the SQL setup scripts. You only need to update the value in this config file, and the SQL scripts will be generated with the same value.

2. The `initialize_user_quota()` SQL function in the generated SQL uses this value to automatically initialize new users with the proper free plan quota when they register.

3. When deploying to different environments, use environment variables to override these settings rather than changing the code.

## Adding New Configuration

When adding new configuration modules:

1. Create a new Python file in the `src/config` directory
2. Document environment variables and defaults
3. Update this README with the new configuration options 