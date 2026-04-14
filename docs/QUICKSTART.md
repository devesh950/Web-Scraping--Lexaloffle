# Quick Start Guide

## 5-Minute Setup

### 1. Install Python 3.8+
Download from [python.org](https://www.python.org/downloads/) if not already installed.

### 2. Create Virtual Environment (Optional but Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure OpenAI API Key

Get your key from: https://platform.openai.com/account/api-keys

Create `.env` file:
```
OPENAI_API_KEY=sk-your-key-here
```

### 5. Run the Project

**Interactive Menu (Recommended for first time):**
```bash
python main.py
```

**Or run specific task:**
```bash
python main.py --task 1  # Scrape games
python main.py --task 2  # Setup RAG database
python main.py --task 3  # Query interface
```

---

## Timeline

| Task | Duration | Status |
|------|----------|--------|
| Install dependencies | 2-3 min | One-time |
| Task 1: Scrape 100 games | 10-15 min | First run |
| Task 2: Setup RAG DB | 2-3 min | One-time |
| Task 3: Query interface | Interactive | As needed |

---

## Sample Queries

Once Task 3 is running, try these:

```
> search puzzle
> popular
> author zack
> code platformer
> inspire roguelike
> exit
```

---

## Troubleshooting

### OpenAI API Key Error
✅ Solution:
1. Sign up at Openai.com
2. Add billing info to account
3. Get API key from https://platform.openai.com/account/api-keys
4. Create `.env` file with `OPENAI_API_KEY=sk-xxxxx`

### Module Not Found Errors
✅ Solution:
```bash
pip install -r requirements.txt --upgrade
```

### Selenium/ChromeDriver Issues
✅ Solution:
```bash
pip install --upgrade webdriver-manager
# chromedriver will auto-install on first run
```

### Connection Timeout on Lexaloffle
✅ Solution:
- Check internet connection
- Try again later (may be rate limiting)
- Web Scraping takes 10-15 minutes - give it time

### CSV Not Found Error
✅ Solution:
Run Task 1 first:
```bash
python main.py --task 1
```

---

## Files Created

After running all tasks:
- `pico8_games.csv` - Dataset of 100 games (1-2 MB)
- `pico8_db/` - Vector database (20-50 MB)
- `logs/` - Execution logs

---

## Performance Notes

**First Run Timeline:**
1. Install dependencies: 2-3 minutes
2. Task 1 (scraping): 10-15 minutes
3. Task 2 (RAG setup): 2-3 minutes
4. **Total: ~20 minutes** for full setup

**Subsequent Runs:**
- Task 3 (queries): Instant start
- Query response: 2-5 seconds average

---

## System Requirements

- **CPU**: Any modern processor
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 500MB free space
- **Network**: Internet required (OpenAI API, Lexaloffle scraping)
- **Browser**: Chrome/Chromium (auto-installed by Selenium)

---

## FAQ

**Q: Can I use this without OpenAI API key?**
A: RAG queries won't work, but Task 1 (scraping) and basic searches will work.

**Q: Can I run just the scraper?**
A: Yes: `python main.py --task 1`

**Q: How much does this cost?**
A: OpenAI embeddings: ~$0.10-0.20 for 100 games. First 3 months free with trial credits.

**Q: Can I scrape more than 100 games?**
A: Yes, modify `task1_scrape.py` line 189 or use `--num_games` parameter.

**Q: How do I contribute or modify?**
A: All source code is in `.py` files. See comments for modification points.

---

## Next Steps

After setup:
1. ✅ Run `python main.py` to start
2. ✅ Follow the menu to execute tasks
3. ✅ Explore the CSV data in Excel/Google Sheets
4. ✅ Use Task 3 to query the RAG database
5. ✅ Prepare submission email to hr@binaire.app

---

**Need help?** Check README.md for detailed documentation.

---
