# Start KIE in Current Folder

Bootstrap a KIE (Kearney Insight Engine) project right here, right now.

## What This Does

When you run `/startkie`, Claude will:
1. Create the KIE folder structure (data/, outputs/, exports/, project_state/)
2. Generate CLAUDE.md with all KIE instructions
3. Generate README.md with quick reference
4. Create .gitignore for proper file handling
5. Begin conversational requirements gathering

## Usage

Just type `/startkie` in any folder and you're ready to work.

## Detection Logic

This command will NOT run if:
- A CLAUDE.md already exists with "KIE Project" in it (already a KIE project)
- You're in the KIE repository itself (project_template/ exists)

In those cases, you'll get a message explaining why.

## What Happens Next

After setup completes, Claude will greet you and ask:
- What client/project are you working on?
- What type of deliverable do you need? (presentation, dashboard, analysis, etc.)
- What data do you have?

Then you're off and running with full KIE capabilities.
