"""
Configuration settings for user quotas.

This module centralizes all quota-related settings used throughout the application.
Settings can be overridden via environment variables.
"""

import os

# Quota limits for different membership tiers
FREE_PLAN_QUOTA = int(os.environ.get("FREE_PLAN_QUOTA", 10))
PREMIUM_PLAN_QUOTA = int(os.environ.get("PREMIUM_PLAN_QUOTA", 50))

# Threshold at which to warn free users they're running low
LOW_QUOTA_THRESHOLD = int(os.environ.get("LOW_QUOTA_THRESHOLD", 3))
