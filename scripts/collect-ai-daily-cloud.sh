#!/bin/bash
# AI Daily Collector - 云端增强版 (获取原文内容)

DATE=$(date +%Y-%m-%d)
OUTPUT_DIR="ai/articles/original/${DATE}"

echo "============================================"
echo "AI Daily Collector (Cloud Enhanced)"
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

IDS=$(curl -s --connect-timeout 10 "${HN_API}/topstories.json" 2>/dev/null | head -30 | tr ',' '\n')

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
        TIMESTAMP=$(date +%s)
        FILENAME="HN_${SCORE}_${ID}.md"
        
        # 获取原文摘要
        TEXT="HN 上评分 ${SCORE} 的热门项目"
        
        cat > "$OUTPUT_DIR/$FILENAME" << EOF
---
title: "$TITLE"
url: "$URL"
source: "Hacker News"
date: "$DATE"
score: "$SCORE"
author: "$BY"
---

# $TITLE

**来源**: [Hacker News](https://news.ycombinator.com/item?id=$ID) | **评分**: $SCORE | **作者**: @$BY

## 摘要

$TEXT

## 原文链接

[$URL]($URL)
EOF
        echo "   ✅ [HN] $TITLE"
    fi
    [ $HN_COUNT -ge 6 ] && break
done
echo "   → Hacker News: $HN_COUNT 条"

# ========== 2. GitHub ==========
echo ""
echo "📥 采集 GitHub..."

GH_TOKEN="$GITHUB_TOKEN"
GH_COUNT=0

if [ -n "$GH_TOKEN" ]; then
    GH_DATA=$(curl -s --connect-timeout 20 \
        -H "Authorization: Bearer $GH_TOKEN" \
        "https://api.github.com/search/repositories?q=AI+agent+cursor&sort=stars&per_page=8" 2>/dev/null)
    
    if echo "$GH_DATA" | grep -q '"items"'; then
        for i in 0 1 2 3 4 5 6 7; do
            NAME=$(echo "$GH_DATA" | jq -r ".items[$i].name // empty" 2>/dev/null)
            FULL_NAME=$(echo "$GH_DATA" | jq -r ".items[$i].full_name // empty" 2>/dev/null)
            DESC=$(echo "$GH_DATA" | jq -r ".items[$i].description // empty" 2>/dev/null)
            STARS=$(echo "$GH_DATA" | jq -r ".items[$i].stargazers_count // 0" 2>/dev/null)
            URL=$(echo "$GH_DATA" | jq -r ".items[$i].html_url // empty" 2>/dev/null)
            LANG=$(echo "$GH_DATA" | jq -r ".items[$i].language // empty" 2>/dev/null)
            
            if [ -n "$NAME" ] && [ -n "$URL" ] && [ "$NAME" != "null" ]; then
                ((GH_COUNT++))
                TOTAL_COUNT=$((TOTAL_COUNT + 1))
                TIMESTAMP=$(date +%s)
                FILENAME="GH_${STARS}_${TIMESTAMP}_${i}.md"
                
                cat > "$OUTPUT_DIR/$FILENAME" << EOF
---
title: "$NAME - $DESC"
url: "$URL"
source: "GitHub"
date: "$DATE"
score: "$STARS"
author: "$FULL_NAME"
---

# $NAME

**来源**: [GitHub]($URL) | **⭐ Stars**: $STARS | **语言**: $LANG

## 项目描述

$DESC

## 原文链接

[$URL]($URL)
EOF
                echo "   ✅ [GH] ⭐$STARS $NAME"
            fi
        done
    fi
fi
echo "   → GitHub: $GH_COUNT 条"

# ========== 3. Hugging Face ==========
echo ""
echo "📥 采集 Hugging Face..."
HF_DATA=$(curl -s --connect-timeout 15 "https://huggingface.co/blog/feed.xml" 2>/dev/null)
HF_COUNT=0

if [ -n "$HF_DATA" ] && echo "$HF_DATA" | grep -q '<item>'; then
    for i in 0 1 2 3 4; do
        TITLE=$(echo "$HF_DATA" | grep -oP '<title>\K[^<]+' 2>/dev/null | sed -n "$((i+2))p")
        LINK=$(echo "$HF_DATA" | grep -oP '<link>\K[^<]+' 2>/dev/null | sed -n "$((i+1))p")
        DESC=$(echo "$HF_DATA" | grep -oP '<description>\K[^<]+' 2>/dev/null | sed -n "$((i+1))p" | sed 's/<[^>]*>//g')
        
        if [ -n "$TITLE" ] && [ -n "$LINK" ]; then
            ((HF_COUNT++))
            TOTAL_COUNT=$((TOTAL_COUNT + 1))
            TIMESTAMP=$(date +%s)
            FILENAME="HF_${TIMESTAMP}_${i}.md"
            
            # 获取内容摘要
            SUMMARY=$(echo "$DESC" | head -c 300)
            
            cat > "$OUTPUT_DIR/$FILENAME" << EOF
---
title: "$TITLE"
url: "$LINK"
source: "Hugging Face"
date: "$DATE"
---

# $TITLE

**来源**: [Hugging Face]($LINK)

## 摘要

$SUMMARY...

## 原文链接

[$LINK]($LINK)
EOF
            echo "   ✅ [HF] $TITLE"
        fi
    done
fi
echo "   → Hugging Face: $HF_COUNT 条"

# ========== 4. MIT Technology Review ==========
echo ""
echo "📥 采集 MIT Technology Review..."
MIT_DATA=$(curl -s --connect-timeout 15 "https://www.technologyreview.com/feed/" 2>/dev/null)
MIT_COUNT=0

if [ -n "$MIT_DATA" ] && echo "$MIT_DATA" | grep -q '<item>'; then
    for i in 0 1 2 3 4; do
        TITLE=$(echo "$MIT_DATA" | grep -oP '<title>\K[^<]+' 2>/dev/null | sed -n "$((i+2))p")
        LINK=$(echo "$MIT_DATA" | grep -oP '<link>\K[^<]+' 2>/dev/null | sed -n "$((i+1))p")
        DESC=$(echo "$MIT_DATA" | grep -oP '<description>\K[^<]+' 2>/dev/null | sed -n "$((i+1))p" | sed 's/<[^>]*>//g' | head -c 500)
        
        if [ -n "$TITLE" ] && [ -n "$LINK" ]; then
            ((MIT_COUNT++))
            TOTAL_COUNT=$((TOTAL_COUNT + 1))
            TIMESTAMP=$(date +%s)
            FILENAME="MIT_${TIMESTAMP}_${i}.md"
            
            cat > "$OUTPUT_DIR/$FILENAME" << EOF
---
title: "$TITLE"
url: "$LINK"
source: "MIT Technology Review"
date: "$DATE"
---

# $TITLE

**来源**: [MIT Technology Review]($LINK)

## 摘要

$DESC...

## 原文链接

[$LINK]($LINK)
EOF
            echo "   ✅ [MIT] $TITLE"
        fi
    done
fi
echo "   → MIT TR: $MIT_COUNT 条"

# ========== 5. Dev.to ==========
echo ""
echo "📥 采集 Dev.to..."
DEVTO_DATA=$(curl -s --connect-timeout 15 "https://dev.to/api/articles?tag=ai&per_page=5" 2>/dev/null)
DEVTO_COUNT=0

if [ -n "$DEVTO_DATA" ]; then
    for i in 0 1 2 3 4; do
        TITLE=$(echo "$DEVTO_DATA" | jq -r ".[$i].title // empty" 2>/dev/null)
        URL=$(echo "$DEVTO_DATA" | jq -r ".[$i].url // empty" 2>/dev/null)
        DESC=$(echo "$DEVTO_DATA" | jq -r ".[$i].description // empty" 2>/dev/null)
        REACTIONS=$(echo "$DEVTO_DATA" | jq -r ".[$i].positive_reactions_count // 0" 2>/dev/null)
        AUTHOR=$(echo "$DEVTO_DATA" | jq -r ".[$i].user.name // empty" 2>/dev/null)
        
        if [ -n "$TITLE" ] && [ -n "$URL" ]; then
            ((DEVTO_COUNT++))
            TOTAL_COUNT=$((TOTAL_COUNT + 1))
            TIMESTAMP=$(date +%s)
            FILENAME="DT_${REACTIONS}_${TIMESTAMP}_${i}.md"
            
            cat > "$OUTPUT_DIR/$FILENAME" << EOF
---
title: "$TITLE"
url: "$URL"
source: "Dev.to"
date: "$DATE"
score: "$REACTIONS"
author: "$AUTHOR"
---

# $TITLE

**来源**: [Dev.to]($URL) | **❤️ reactions**: $REACTIONS | **作者**: $AUTHOR

## 摘要

$DESC

## 原文链接

[$URL]($URL)
EOF
            echo "   ✅ [DT] $TITLE"
        fi
    done
fi
echo "   → Dev.to: $DEVTO_COUNT 条"

# ========== 6. ArXiv ==========
echo ""
echo "📥 采集 ArXiv AI 论文..."
ARXIV_DATA=$(curl -s --connect-timeout 20 -L \
    "https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=6" 2>/dev/null)
ARXIV_COUNT=0

if [ -n "$ARXIV_DATA" ] && echo "$ARXIV_DATA" | grep -q '<entry>'; then
    for i in 0 1 2 3 4 5; do
        TITLE=$(echo "$ARXIV_DATA" | grep -oP '<title>\K[^<]+' 2>/dev/null | sed -n "$((i*4+1))p")
        URL=$(echo "$ARXIV_DATA" | grep -oP '<id>\K[^<]+' 2>/dev/null | sed -n "$((i+1))p")
        SUMMARY=$(echo "$ARXIV_DATA" | grep -oP '<summary>\K[^<]+' 2>/dev/null | sed -n "$((i+1))p" | tr '\n' ' ' | head -c 500)
        AUTHORS=$(echo "$ARXIV_DATA" | grep -oP '<author><name>\K[^<]+' 2>/dev/null | sed -n "$((i+1))p")
        
        if [ -n "$TITLE" ] && [ -n "$URL" ]; then
            ((ARXIV_COUNT++))
            TOTAL_COUNT=$((TOTAL_COUNT + 1))
            TIMESTAMP=$(date +%s)
            FILENAME="ARXIV_${TIMESTAMP}_${i}.md"
            
            cat > "$OUTPUT_DIR/$FILENAME" << EOF
---
title: "$TITLE"
url: "$URL"
source: "ArXiv"
date: "$DATE"
author: "$AUTHORS"
---

# $TITLE

**来源**: [ArXiv]($URL) | **作者**: $AUTHORS

## 摘要

$SUMMARY...

## 原文链接

[$URL]($URL)
EOF
            echo "   ✅ [ArXiv] $TITLE"
        fi
    done
fi
echo "   → ArXiv: $ARXIV_COUNT 条"

echo ""
echo "============================================"
echo "📊 采集完成! 总计: $TOTAL_COUNT 条"
echo "   - HN: $HN_COUNT | GH: $GH_COUNT | HF: $HF_COUNT"
echo "   - MIT: $MIT_COUNT | DT: $DEVTO_COUNT | ArXiv: $ARXIV_COUNT"
echo "============================================"

echo ""
echo "✅ 完成! 文件保存于: $OUTPUT_DIR/"
