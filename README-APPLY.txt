Review Insights - ALL updates in one zip
========================================
This zip contains the FINAL version of every file changed by the five earlier
patches (cost, trends, NLP, star-only, signals). Apply it ONCE - no ordering.

It does NOT include: .env files, Dockerfiles, docker-compose.yml, .gitignore,
requirements.txt, package.json, or any file the updates never touched. Those stay
exactly as they are in your project. It adds no new packages.

Apply it from your project root (the folder that contains backend/ and frontend/):

    unzip -o ~/Downloads/review-insights-all-updates.zip

Use the terminal command above. Do NOT drag the folders in Finder: Finder's
"Replace" swaps out the whole folder and deletes the files this zip doesn't contain.

Then rebuild:

    docker compose down
    docker compose up --build
