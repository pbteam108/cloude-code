from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from tavily import TavilyClient
import anthropic
from dotenv import load_dotenv
import os
import re
import json

load_dotenv()

app = FastAPI()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


class SearchRequest(BaseModel):
    category: str
    custom_fields: List[str] = []


@app.post("/api/search")
async def search_competitors(request: SearchRequest):
    category = request.category.strip()
    if not category:
        raise HTTPException(status_code=400, detail="カテゴリーを入力してください")

    query = f"{category} 商品 公式 メーカー 会社名 特徴 価格 内容量"

    response = tavily.search(
        query=query,
        search_depth="advanced",
        max_results=10,
        include_images=True,
        include_answer=True,
    )

    images = response.get("images", [])
    results = response.get("results", [])

    competitors = extract_with_claude(category, results, images, request.custom_fields)

    return {
        "category": category,
        "competitors": competitors,
        "summary": response.get("answer", ""),
        "custom_fields": request.custom_fields,
    }


def extract_with_claude(category: str, results: list, images: list, custom_fields: list) -> list:
    results_text = ""
    for i, r in enumerate(results[:10]):
        results_text += f"\n--- 結果{i+1} ---\n"
        results_text += f"タイトル: {r.get('title', '')}\n"
        results_text += f"URL: {r.get('url', '')}\n"
        results_text += f"内容: {r.get('content', '')[:600]}\n"

    custom_fields_json = ""
    if custom_fields:
        custom_fields_json = ",\n" + ",\n".join([f'    "{f}": "{f}に関する情報（なければ空文字）"' for f in custom_fields])

    prompt = f"""以下は「{category}」カテゴリの商品に関するWeb検索結果です。
実際の競合製品を最大8件抽出し、JSON配列で返してください。

ルール:
- 比較サイト・ランキング記事のタイトルは商品名にしない
- 実際の商品名・ブランド名・製品名のみを使用
- 重複する商品は1件にまとめる
- URLは検索結果に含まれるものだけを使用（不明なら空文字）
- 価格は「¥1,000」形式、不明なら空文字

{results_text}

以下のJSON形式のみを返してください（説明文不要）:
[
  {{
    "name": "商品名",
    "company": "メーカー・会社名",
    "price": "価格",
    "volume": "内容量",
    "features": "主な特徴（100文字程度）",
    "url": "URL"{custom_fields_json}
  }}
]"""

    try:
        message = claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )

        text = message.content[0].text.strip()
        json_match = re.search(r'\[[\s\S]*\]', text)
        items = json.loads(json_match.group() if json_match else text)

        for i, item in enumerate(items):
            item["image"] = images[i] if i < len(images) else ""
            for field in custom_fields:
                val = item.pop(field, "") or item.get(f"custom_{field}", "")
                item[f"custom_{field}"] = val

        return items[:8]

    except Exception:
        return extract_with_regex(results, images, custom_fields)


def extract_with_regex(results: list, images: list, custom_fields: list) -> list:
    competitors = []
    seen = set()
    image_idx = 0

    for result in results:
        title = result.get("title", "").strip()
        url = result.get("url", "")
        content = result.get("content", "")

        product_name = extract_product_name(title)
        if not product_name or product_name.lower() in seen:
            continue
        seen.add(product_name.lower())

        image_url = images[image_idx] if image_idx < len(images) else ""
        image_idx += 1

        item = {
            "name": product_name,
            "company": extract_company(content, url),
            "price": extract_price(content),
            "volume": extract_volume(content),
            "features": content[:200] + "..." if len(content) > 200 else content,
            "url": url,
            "image": image_url,
        }

        for field in custom_fields:
            item[f"custom_{field}"] = extract_custom_field(content, field)

        competitors.append(item)
        if len(competitors) >= 8:
            break

    return competitors


def extract_product_name(title: str) -> str:
    title = re.sub(r"[\|｜\-–—].*$", "", title).strip()
    title = re.sub(r"(の比較|比較|レビュー|とは|料金|評判|一覧|ランキング|公式|サイト|ショップ|通販).*$", "", title).strip()
    return title[:40] if title else ""


def extract_company(content: str, url: str) -> str:
    patterns = [
        r"(?:メーカー|製造元|発売元|販売元|ブランド|会社名|運営会社)[：:]\s*([^\s、。,\n]{2,20})",
        r"([^\s、。,\n]{2,15})(?:株式会社|有限会社|合同会社|食品|フーズ|コーポレーション)",
        r"(?:株式会社|有限会社|合同会社)([^\s、。,\n]{2,15})",
    ]
    for p in patterns:
        m = re.search(p, content)
        if m:
            return m.group(1).strip()[:30]
    domain_match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if domain_match:
        parts = domain_match.group(1).split(".")
        return parts[0] if parts else ""
    return ""


def extract_price(content: str) -> str:
    patterns = [r"([\d,]+)\s*円", r"¥\s*([\d,]+)", r"￥\s*([\d,]+)"]
    for p in patterns:
        for m in re.finditer(p, content):
            val = m.group(1).replace(",", "")
            if val.isdigit() and 100 <= int(val) <= 100000:
                return f"¥{int(val):,}"
    return ""


def extract_volume(content: str) -> str:
    m = re.search(r"([\d.]+\s*(?:g|kg|ml|mL|L|ℓ|oz|個|枚|本|袋|缶|粒|食|包))", content)
    return m.group(1).strip() if m else ""


def extract_custom_field(content: str, field: str) -> str:
    escaped = re.escape(field)
    patterns = [
        rf"{escaped}[：:\s]+([^\n。、,，]{{1,60}})",
        rf"{escaped}は[、,]?\s*([^\n。、,，]{{1,60}})",
        rf"【{escaped}】\s*([^\n。]{{1,60}})",
    ]
    for p in patterns:
        m = re.search(p, content)
        if m:
            return m.group(1).strip()
    return ""


app.mount("/", StaticFiles(directory="static", html=True), name="static")
