#!/bin/bash
# AI Daily Collector - 云端增强版 (使用 jina.ai 提取原文)

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

# 提取文章内容函数 (使用 jina.ai)
extract_content() {
    local URL="$1"
    # 移除协议头，只保留域名和路径
    local CLEAN_URL=$(echo "$URL" | sed 's|https://||' | sed 's|http://||')
    local CONTENT=$(curl -s --max-time 15 "https://r.jina.ai/http://${CLEAN_URL}" 2>/dev/null)
    echo "$CONTENT"
}

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
        
        # 提取原文
        CONTENT=""
        if [ -n "$URL" ]; then
            CONTENT=$(extract_content "$URL")
        fi
        
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

## 原文内容

$CONTENT

---
*自动采集于 $DATE*
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
                
                # 提取 README 内容
                CONTENT=""
                if [ -n "$URL" ]; then
                    CONTENT=$(extract_content "$URL")
                fi
                
                cat > "$OUTPUT_DIR/$FILENAME" << EOF
---
title: "$NAME"
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

## 原文 README

$CONTENT

---
*自动采集于 $DATE*
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
        
        if [ -n "$TITLE" ] && [ -n "$LINK" ]; then
            ((HF_COUNT++))
            TOTAL_COUNT=$((TOTAL_COUNT + 1))
            TIMESTAMP=$(date +%s)
            FILENAME="HF_${TIMESTAMP}_${i}.md"
            
            # 提取内容
            CONTENT=$(extract_content "$LINK")
            
            cat > "$OUTPUT_DIR/$FILENAME" << EOF
---
title: "$TITLE"
url: "$LINK"
source: "Hugging Face"
date: "$DATE"
---

# $TITLE

**来源**: [Hugging Face]($LINK)

## 原文内容

$CONTENT

---
*自动采集于 $DATE*
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
        
        if [ -n "$TITLE" ] && [ -n "$LINK" ]; then
            ((MIT_COUNT++))
            TOTAL_COUNT=$((TOTAL_COUNT + 1))
            TIMESTAMP=$(date +%s)
            FILENAME="MIT_${TIMESTAMP}_${i}.md"
            
            # 提取内容
            CONTENT=$(extract_content "$LINK")
            
            cat > "$OUTPUT_DIR/$FILENAME" << EOF
---
title: "$TITLE"
url: "$LINK"
source: "MIT Technology Review"
date: "$DATE"
---

# $TITLE

**来源**: [MIT Technology Review]($LINK)

## 原文内容

$CONTENT

---
*自动采集于 $DATE*
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
            
            # 提取内容
            CONTENT=$(extract_content "$URL")
            
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

## 原文内容

$CONTENT

---
*自动采集于 $DATE*
EOF
            echo "   ✅ [DT] $TITLE"
        fi
    done
fi
echo "   → Dev.to: $DEVTO_COUNT 条"

echo ""
echo "============================================"
echo "📊 采集完成! 总计: $TOTAL_COUNT 条"
echo "   - HN: $HN_COUNT | GH: $GH_COUNT | HF: $HF_COUNT"
echo "   - MIT: $MIT_COUNT | DT: $DEVTO_COUNT"
echo "============================================"

echo ""
echo "✅ 完成! 文件保存于: $OUTPUT_DIR/"
echo ""
echo "🔄 提交到 GitHub..."

# 配置 git 用户信息（使用 GitHub Actions bot）
git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"

# 使用 GITHUB_TOKEN 进行认证
git add $OUTPUT_DIR/
git commit -m "AI Daily: $DATE - $TOTAL_COUNT 条内容" || echo "无新内容"

# 配置远程 URL 使用 token 认证
git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/xxl115/ai-daily-collector.git"
git push origin master || echo "推送失败"

echo ""
echo "✅ 全部完成!"
