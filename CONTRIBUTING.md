# Contributing to Awesome Developer Conferences

Thank you for considering contributing to the **Awesome Developer Conferences** directory! 

This repo is maintained by [Infrasity](https://infrasity.com) and updated daily via GitHub Actions.

This document serves as a set of guidelines for contributing to the repository.

---
## Ways to Contribute
### 1. Submit an Event

If you know of a developer conference that isn't listed here yet, you can easily add it yourself! The event tables live in one file per region under [`events/`](./events). `README.md` is only an overview that is rebuilt every night, so don't edit it by hand.

1. **Fork the repository** to your own GitHub account.
2. Open the file for the right **region** in `events/` (`asia.md`, `europe.md`, `north-america.md`, etc.; use `virtual-online.md` for online events).
3. Add a new row to the Markdown table in chronological order based on the event's date.
4. Follow the exact table format:
   ```markdown
   | Event Name |  YYYY-MM-DD to YYYY-MM-DD | City, Country | [↗](link) |
   ```
5. Submit a **Pull Request** with a short description of the event you added!

---

### 2. The Automated Fetchers

This repository uses automated Python scripts to fetch events from major conference directories every night at midnight UTC via GitHub Actions.

If you are a developer, you can contribute by adding new automated scrapers!
* All fetcher scripts are located in the `fetchers/` directory.
* If you want to add a new source, simply create a new Python script (e.g. `my_source.py`) that parses the website and writes its events to an `events_<source>.json` file. `aggregate.py` merges those files into the region tables.
* Once your script is built, add it to the `.github/workflows/update-all-events.yml` GitHub Action file so it runs automatically.

---

### 3. Improve the Code

If you want to improve existing Python fetchers, fix bugs, or add new ones, here is how you can set up the project locally on your machine:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Infrasity-Labs/awesome-developer-conferences.git
   cd awesome-developer-conferences
   ```

2. **Set up environment variables** (if required):
   If you are testing scripts that require API keys, create a `.env` file in the root directory:
   ```bash
   touch .env
   # Add your API keys inside, for example:
   # GEMINI_API_KEY=your_secret_key_here
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run a fetcher locally to test your changes**:
   ```bash
   python fetchers/developer_events.py
   ```

5. Rebuild the generated files and check they updated correctly, then submit a Pull Request:
   ```bash
   python aggregate.py              # merge events_*.json into events/<region>.md
   python dedupe_events.py          # drop duplicate rows
   python build_country_index.py    # countries/*.md
   python build_readme.py           # README.md and .github/assets/*.svg
   python -m unittest               # run the tests
   ```

**Project layout**

```text
events/            one table per region (the data, editable by hand)
countries/         generated: upcoming in-person events per country
fetchers/          one script per source, each writes events_<source>.json
aggregate.py       merges fetcher output into events/
checks/            date, link and spelling checks (run on events/)
build_readme.py    generates README.md; readme_assets.py draws the SVGs in .github/assets/
```

---

### 4. Pull Request Guidelines

* **Keep it relevant:** Only add conferences, hackathons, or summits that are strictly relevant to software engineers, developers, data scientists, or IT professionals.
* **No spam:** Please do not add promotional spam, paid bootcamps, or events that do not have a public registration page.
* **Clean Code:** If you are contributing Python code to the `fetchers/` directory, please ensure your code is well-commented and handles network errors gracefully.

---

### 5. Found a Bug?

If you spot a broken link, a cancelled event, or a bug in one of our Python fetchers, please [open an Issue](https://github.com/Infrasity-Labs/awesome-developer-conferences/issues/new) on the repository so we can fix it!

Thank you for helping Infrasity build the best developer event directory on the internet!
