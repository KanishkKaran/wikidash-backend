# 📚 WikiDash Backend

This is the Flask backend powering **WikiDash**, an open-source OSINT dashboard for exploring hidden insights about Wikipedia articles.

It exposes APIs to retrieve:

- Article summaries and metadata
- Pageview history
- Editor statistics and top contributors
- Edit timelines and revert patterns
- Citation analysis (including domain-level insights)
- Country-of-origin estimates for anonymous edits
- Future: Editor networks & reputation scoring

---

## 🚀 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/article?title=...` | Summary, metadata, and pageviews |
| `/api/citations?title=...` | Citation count and domain breakdown |
| `/api/editors?title=...` | Top contributors with edit counts |
| `/api/edits?title=...` | Total edit count |
| `/api/edit-timeline?title=...` | Timeline of edit frequency |
| `/api/reverts?title=...` | Revert activity per day |
| `/api/reverters?title=...` | Editors most involved in reverts |
| `/api/editor-countries?title=...` | Country origins of anonymous edits |

---

For Local Setup


1. ```git clone https://github.com/KanishkKaran/wikidash-backend.git```

2. ```cd wikidash-backend```

3. ```python3 -m venv venv```

4. ```source venv/bin/activate```

5. ```pip install -r requirements.txt```

6. ```python app.py```
