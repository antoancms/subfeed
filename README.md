# README.md

# 🔗 ShareKit Clone – Custom Facebook Link Preview Generator

This project allows you to generate custom Facebook/Twitter/Open Graph previews (title, description, image) for any URL. Think of it as your personal ShareKit.

Live hosted previews work great when shared on social media!

---

## ✨ Features
- Custom title, description, and image
- Auto-generated short preview URL
- Facebook-ready Open Graph metadata
- Instant redirection after social sharing

---

## 🚀 How to Use Locally

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
python app.py
```
Visit `http://localhost:5000` in your browser.

### 3. Create Previews
- Fill in a real destination URL, title, description, and image.
- A new preview URL will be created like `/p/abc123`
- Share that short URL to show your custom preview.

---

## 🌐 Deploy Free on Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

**Render Setup:**
- Build Command: `pip install -r requirements.txt`
- Start Command: `python app.py`
- Python Environment: 3.10+

---

## 📁 Project Structure
```
custom_sharekit/
├── app.py
├── data.json
├── requirements.txt
├── static/
│   └── style.css
├── templates/
│   ├── index.html
│   └── og_page.html
```

---

## ✅ License
MIT – free for personal and commercial use.

---

Enjoy customizing how links look on social media! 🚀
