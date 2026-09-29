# Celebration Copilot - Party Planning Agent

An AI assistant that helps users plan events by generating creative themes, fetching visual mood boards, estimating food/drink budgets, and drafting Partiful invites.

## Tools Included

1. `get_theme_moodboard`: Searches Unsplash REST API for high-res party photos and generates targeted Pinterest search links.
2. `calculate_party_budget`: Estimates total budget, drink counts (wine/beer/cocktails), food portions, and ice needs based on guest count and duration.
3. `generate_partiful_kit`: Generates invitation copy, titles, and direct setup URLs for Partiful.

## Local Running Instructions

```bash
# Install dependencies and run locally
uv run app.py
