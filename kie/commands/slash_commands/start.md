# /start

---
name: start
description: Start a new KIE project
---

Start a new KIE project with guided setup.

## Usage

Just type `/start` and KIE will guide you through:

1. **Project Setup** - Create project structure
2. **Data Upload** - Add your data files
3. **Requirements** - Quick interview about what you need
4. **Analysis** - Automatic EDA on your data

## What Happens

When you run `/start`:

```
KIE: Welcome! Let's set up your project.

What do you want to call this project?
> Customer Analysis Q4

KIE: Got it - "Customer Analysis Q4"

Do you have data to analyze?
1. Yes, I have a file path
2. Yes, I'll paste/drag it
3. No, I'll add data later

> 1

KIE: What's the path to your data?
> /Users/me/Downloads/sales.csv

KIE: Found sales.csv (1,234 rows, 8 columns)

[Auto-EDA runs and shows summary]

What are you trying to understand from this data?
> Which products are selling best by region

KIE: Perfect. I've set up your project:
- Project: Customer Analysis Q4
- Data: sales.csv
- Question: Product performance by region

Ready to analyze. Run /analyze to generate insights.
```

## Project Structure Created

```
my-project/
├── data/
│   └── sales.csv          # Your data
├── outputs/
│   └── eda_profile.yaml   # Auto-generated EDA
├── exports/               # Final deliverables go here
└── project_state/
    └── spec.yaml          # Project requirements
```

## For Existing Projects

If you run `/start` in a project that already has data:

```
KIE: I found existing data:
- data/sales.csv (1,234 rows)
- data/customers.xlsx (567 rows)

Would you like to:
1. Analyze existing data
2. Add more data
3. Start fresh

> 1
```

## Next Steps

After `/start`:
- `/eda` - Deep dive into your data
- `/analyze` - Generate insights
- `/build` - Create charts, dashboard, or presentation
