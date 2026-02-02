#!/bin/bash
# AI Daily Collector - 云端版 (GitHub Actions)
# 可以访问被墙的网站: Hugging Face, Reddit, Product Hunt

DATE=$(date +%Y-%m-%d)
OUTPUT_DIR="ai/articles/original/${DATE}"

echo "============================================"
echo "AI Daily Collector (Cloud Edition)"
echo "日期: $DATE"
echo "============================================"
echo ""

mkdir -p "$OUTPUT_DIR"
TOTAL_COUNT=0
KEYWORDS="AI|Claude|llm|agent|cursor|programming|developer|machine learning|software"

# ========== 1. Hacker News ==========
echo "📥 采集 Hacker News..."
HN_API="https://hacker-news.firebaseio.com/v0"
HN_COUNT=0

IDS=$(curl -s --connect-timeout 10 "${HN_API}/topstories.json" 2>/dev/null | head -50 | tr ',' '\n')

for ID in $IDS; do
    STORY=$(curl -s --connect-timeout 5 "${HN_API}/item/${ID}.json" 2>/dev/null)
    [ -z "$STORY" ] && continue
    
    TITLE=$(echo "$STORY" | jq -r '.title' 2>/dev/null)
    URL=$(echo "$STORY" | jq -r '.url' 2>/dev/null)
    SCORE=$(echo "$STORY" | jq -r '.score' 2>/dev/null)
    BY=$(echo "$STORY" | jq -r '.by' 2>/dev/null)
    
    if echo "$TITLE" | grep -qiE "$KEYWORDS"; then
        ((HN_COUNT++))
        TOTAL_COUNT=$((TOTAL_COUNT + 1))
        FILENAME="HN_${SCORE}_${ID}.txt"
        echo "Title: $TITLE" > "$OUTPUT_DIR/$FILENAME"
        echo "URL: $URL" >> "$OUTPUT_DIR/$FILENAME"
        echo "Score: $SCORE" >> "$OUTPUT_DIR/$FILENAME"
        echo "Author: $BY" >> "$OUTPUT_DIR/$FILENAME"
        echo "Source: Hacker News" >> "$OUTPUT_DIR/$FILENAME"
        echo "Date: $DATE" >> "$OUTPUT_DIR/$FILENAME"
    fi
    [ $HN_COUNT -ge 8 ] && break
done
echo "   → Hacker News: $HN_COUNT 条"

# ========== 2. GitHub ==========
echo ""
echo "📥 采集 GitHub..."

# GitHub Token from env
GH_TOKEN="$GITHUB_TOKEN"
GH_COUNT=0

if [ -n "$GH_TOKEN" ]; then
    GH_DATA=$(curl -s --connect-timeout 20 \
        -H "Authorization: Bearer $GH_TOKEN" \
        "https://api.github.com/search/repositories?q=AI+agent+cursor&sort=stars&per_page=8" 2>/dev/null)
    
    if echo "$GH_DATA" | grep -q '"items"'; then
        for i in 0 1 2 3 4 5 6 7; do
            NAME=$(echo "$GH_DATA" | jq -r ".items[$i].name // empty" 2>/dev/null)
            DESC=$(echo "$GH_DATA" | jq -r ".items[$i].description // empty" 2>/dev/null)
            STARS=$(echo "$GH_DATA" | jq -r ".items[$i].stargazers_count // 0" 2>/dev/null)
            URL=$(echo "$GH_DATA" | jq -r ".items[$i].html_url // empty" 2>/dev/null)
            
            if [ -n "$NAME" ] && [ -n "$URL" ] && [ "$NAME" != "null" ]; then
                ((GH_COUNT++))
                TOTAL_COUNT=$((TOTAL_COUNT + 1))
                TIMESTAMP=$(date +%s)
                FILENAME="GH_${STARS}_${TIMESTAMP}_${i}.txt"
                echo "Title: $NAME - $DESC" > "$OUTPUT_DIR/$FILENAME"
                echo "URL: $URL" >> "$OUTPUT_DIR/$FILENAME"
                echo "Score: $STARS" >> "$OUTPUT_DIR/$FILENAME"
                echo "Source: GitHub" >> "$OUTPUT_DIR/$FILENAME"
                echo "Date: $DATE" >> "$OUTPUT_DIR/$FILENAME"
            fi
        done
    fi
fi
echo "   → GitHub: $GH_COUNT 条"

# ========== 3. Hugging Face (云端可访问) ==========
echo ""
echo "📥 采集 Hugging Face..."
HF_DATA=$(curl -s --connect-timeout 15 "https://huggingface.co/blog/feed.xml" 2>/dev/null)
HF_COUNT=0

if [ -n "$HF_DATA" ] && echo "$HF_DATA" | grep -q '<item>'; then
    for i in 0 1 2 3 4; do
        TITLE=$(echo "$HF_DATA" | grep -oP '<title>\K[^<]+' 2>/dev/null | sed -n "$((i+2))p")
        LINK=$(echo "$HF_DATA" | grep -oP '<link>\K[^<]+' 2>/dev/null | sed -n "$((i+1))p")
        
        if [ -n "$TITLE" ] && [ -n "$LINK" ]; then
            ((HF_COUNT++))
            TOTAL_COUNT=$((TOTAL_COUNT + 1))
            TIMESTAMP=$(date +%s)
            FILENAME="HF_${TIMESTAMP}_${i}.txt"
            echo "Title: $TITLE" > "$OUTPUT_DIR/$FILENAME"
            echo "URL: $LINK" >> "$OUTPUT_DIR/$FILENAME"
            echo "Score: 0" >> "$OUTPUT_DIR/$FILENAME"
            echo "Source: Hugging Face" >> "$OUTPUT_DIR/$FILENAME"
            echo "Date: $DATE" >> "$OUTPUT_DIR/$FILENAME"
        fi
    done
fi
echo "   → Hugging Face: $HF_COUNT 条"

# ========== 4. Reddit (云端可访问) ==========
echo ""
echo "📥 采集 Reddit..."
REDDIT_SUBS=("ClaudeAI" "LocalLLaMA" "Artificial" "Programming")
REDDIT_COUNT=0

for SUB in "${REDDIT_SUBS[@]}"; do
    RSS_URL="https://www.reddit.com/r/${SUB}/.rss"
    RSS_DATA=$(curl -s --connect-timeout 10 "$RSS_URL" 2>/dev/null)
    
    if echo "$RSS_DATA" | grep -q '<item>'; then
        for i in 0 1 2; do
            TITLE=$(echo "$RSS_DATA" | grep -oP '<title>\K[^<]+' 2>/dev/null | sed -n "$((i+2))p")
            LINK=$(echo "$RSS_DATA" | grep -oP '<link>\K[^<]+' 2>/dev/null | sed -n "$((i+1))p")
            
            if [ -n "$TITLE" ] && [ -n "$LINK" ]; then
                ((REDDIT_COUNT++))
                TOTAL_COUNT=$((TOTAL_COUNT + 1))
                TIMESTAMP=$(date +%s)
                FILENAME="RD_${TIMESTAMP}_${SUB}_${i}.txt"
                echo "Title: $TITLE" > "$OUTPUT_DIR/$FILENAME"
                echo "URL: $LINK" >> "$OUTPUT_DIR/$FILENAME"
                echo "Score: 0" >> "$OUTPUT_DIR/$FILENAME"
                echo "Source: Reddit r/$SUB" >> "$OUTPUT_DIR/$FILENAME"
                echo "Date: $DATE" >> "$OUTPUT_DIR/$FILENAME"
            fi
        done
    fi
done
echo "   → Reddit: $REDDIT_COUNT 条"

# ========== 5. Product Hunt (云端可访问) ==========
echo ""
echo "📥 采集 Product Hunt..."
PH_URL="https://www.producthunt.com/feed"
PH_DATA=$(curl -s --connect-timeout 15 "$PH_URL" 2>/dev/null)
PH_COUNT=0

if [ -n "$PH_DATA" ] && echo "$PH_DATA" | grep -q '<item>'; then
    for i in 0 1 2 3 4; do
        TITLE=$(echo "$PH_DATA" | grep -oP '<title>\K[^<]+' 2>/dev/null | sed -n "$((i+2))p")
        LINK=$(echo "$PH_DATA" | grep -oP '<link>\K[^<]+' 2>/dev/null | sed -n "$((i+1))p")
        
        if [ -n "$TITLE" ] && [ -n "$LINK" ]; then
            ((PH_COUNT++))
            TOTAL_COUNT=$((TOTAL_COUNT + 1))
            TIMESTAMP=$(date +%s)
            FILENAME="PH_${TIMESTAMP}_${i}.txt"
            echo "Title: $TITLE" > "$OUTPUT_DIR/$FILENAME"
            echo "URL: $LINK" >> "$OUTPUT_DIR/$FILENAME"
            echo "Score: 0" >> "$OUTPUT_DIR/$FILENAME"
            echo "Source: Product Hunt" >> "$OUTPUT_DIR/$FILENAME"
            echo "Date: $DATE" >> "$OUTPUT_DIR/$FILENAME"
        fi
    done
fi
echo "   → Product Hunt: $PH_COUNT 条"

# ========== 6. MIT Technology Review ==========
echo ""
echo "📥 采集 MIT Technology Review..."
MIT_DATA=$(curl -s --connect-timeout 15 "https://www.technologyreview.com/feed/" 2>/dev/null)
MIT_COUNT=0

if [ -n "$MIT_DATA" ] && echo "$MIT_DATA" | grep -q '<item>'; then
    for i in 0 1 2 3 4; do
        TITLE=$(echo "$MIT_DATA" | grep -oP '<title>\K[^<]+' 2>/dev/null | sed -n "$((i+2))p")
        LINK=$(echo "$MIT_DATA" | grep -oP '<link>\K[^<]+' 2>/dev/null | sed -n "$((i+1))p")
        
        if [ -n "$TITLE" ] && [ -n "$LINK" ]; then
            ((MIT_COUNT++))
            TOTAL_COUNT=$((TOTAL_COUNT + 1))
            TIMESTAMP=$(date +%s)
            FILENAME="MIT_${TIMESTAMP}_${i}.txt"
            echo "Title: $TITLE" > "$OUTPUT_DIR/$FILENAME"
            echo "URL: $LINK" >> "$OUTPUT_DIR/$FILENAME"
            echo "Score: 0" >> "$OUTPUT_DIR/$FILENAME"
            echo "Source: MIT Technology Review" >> "$OUTPUT_DIR/$FILENAME"
            echo "Date: $DATE" >> "$OUTPUT_DIR/$FILENAME"
        fi
    done
fi
echo "   → MIT TR: $MIT_COUNT 条"

# ========== 7. ArXiv ==========
echo ""
echo "📥 采集 ArXiv AI 论文..."
ARXIV_DATA=$(curl -s --connect-timeout 20 -L \
    "https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=8" 2>/dev/null)
ARXIV_COUNT=0

if [ -n "$ARXIV_DATA" ] && echo "$ARXIV_DATA" | grep -q '<entry>'; then
    for i in 0 1 2 3 4 5 6 7; do
        TITLE=$(echo "$ARXIV_DATA" | grep -oP '<title>\K[^<]+' 2>/dev/null | sed -n "$((i*4+1))p")
        URL=$(echo "$ARXIV_DATA" | grep -oP '<id>\K[^<]+' 2>/dev/null | sed -n "$((i+1))p")
        
        if [ -n "$TITLE" ] && [ -n "$URL" ]; then
            ((ARXIV_COUNT++))
            TOTAL_COUNT=$((TOTAL_COUNT + 1))
            TIMESTAMP=$(date +%s)
            FILENAME="ARXIV_${TIMESTAMP}_${i}.txt"
            echo "Title: $TITLE" > "$OUTPUT_DIR/$FILENAME"
            echo "URL: $URL" >> "$OUTPUT_DIR/$FILENAME"
            echo "Score: 0" >> "$OUTPUT_DIR/$FILENAME"
            echo "Source: ArXiv AI" >> "$OUTPUT_DIR/$FILENAME"
            echo "Date: $DATE" >> "$OUTPUT_DIR/$FILENAME"
        fi
    done
fi
echo "   → ArXiv: $ARXIV_COUNT 条"

# ========== 8. Dev.to ==========
echo ""
echo "📥 采集 Dev.to..."
DEVTO_DATA=$(curl -s --connect-timeout 15 "https://dev.to/api/articles?tag=ai&per_page=5" 2>/dev/null)
DEVTO_COUNT=0

if [ -n "$DEVTO_DATA" ]; then
    for i in 0 1 2 3 4; do
        TITLE=$(echo "$DEVTO_DATA" | jq -r ".[$i].title // empty" 2>/dev/null)
        URL=$(echo "$DEVTO_DATA" | jq -r ".[$i].url // empty" 2>/dev/null)
        REACTIONS=$(echo "$DEVTO_DATA" | jq -r ".[$i].positive_reactions_count // 0" 2>/dev/null)
        
        if [ -n "$TITLE" ] && [ -n "$URL" ]; then
            ((DEVTO_COUNT++))
            TOTAL_COUNT=$((TOTAL_COUNT + 1))
            TIMESTAMP=$(date +%s)
            FILENAME="DT_${REACTIONS}_${TIMESTAMP}_$i.txt"
            echo "Title: $TITLE" > "$OUTPUT_DIR/$FILENAME"
            echo "URL: $URL" >> "$OUTPUT_DIR/$FILENAME"
            echo "Score: $REACTIONS" >> "$OUTPUT_DIR/$FILENAME"
            echo "Source: Dev.to" >> "$OUTPUT_DIR/$FILENAME"
            echo "Date: $DATE" >> "$OUTPUT_DIR/$FILENAME"
        fi
    done
fi
echo "   → Dev.to: $DEVTO_COUNT 条"

echo ""
echo "============================================"
echo "📊 采集完成! 总计: $TOTAL_COUNT 条"
echo "   - HN: $HN_COUNT | GH: $GH_COUNT | HF: $HF_COUNT"
echo "   - RD: $REDDIT_COUNT | PH: $PH_COUNT | MIT: $MIT_COUNT"
echo "   - ArXiv: $ARXIV_COUNT | DT: $DEVTO_COUNT"
echo "============================================"

# 同步到 Notion (如果配置了)
if [ -n "$NOTION_API_KEY" ] && [ -n "$NOTION_DB_ID" ]; then
    echo ""
    echo "🔄 同步到 Notion..."
    python3 << NOTION_SYNC
import requests
import os
from datetime import datetime

date = "$DATE"
notion_key = os.environ.get("NOTION_API_KEY")
db_id = os.environ.get("NOTION_DB_ID")

headers = {
    "Authorization": f"Bearer {notion_key}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

data = {
    "parent": {"database_id": db_id},
    "properties": {
        "Name": {"title": [{"text": {"content": f"AI Daily - {date}"}}]},
        "Date": {"date": {"start": date}},
        "Tags": {"multi_select": [{"name": "AI Daily"}, {"name": "Auto"}]}
    },
    "children": [
        {"object": "block", "type": "paragraph", "paragraph": {
            "rich_text": [{"text": {"content": f"采集完成! HN:{HN_COUNT} GH:{GH_COUNT} HF:{HF_COUNT} RD:{REDDIT_COUNT} PH:{PH_COUNT} MIT:{MIT_COUNT} ArXiv:{ARXIV_COUNT} DT:{DEVTO_COUNT}"}}]
        }}
    ]
}

resp = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
print(f"Notion Sync: {'✅ 成功' if resp.status_code == 200 else '❌ 失败'}")
print(f"Page ID: {resp.json().get('id', 'N/A')}")
NOTION_SYNC
fi

echo ""
echo "✅ 完成!"
