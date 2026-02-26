from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from tavily import TavilyClient
from dotenv import load_dotenv
import os
import re

load_dotenv()

app = FastAPI()
client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


class SearchRequest(BaseModel):
    category: str
    custom_fields: List[str] = []


@app.post("/api/search")
async def search_competitors(request: SearchRequest):
    category = request.category.strip()
    if not category:
        raise HTTPException(status_code=400, detail="カテゴリーを入力してください")

    query = f"{category} 商品 公式 メーカー 会社名 特徴 価格 内容量"

    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=10,
        include_images=True,
        include_answer=True,
    )

    images = response.get("images", [])
    competitors = []
    seen = set()
    image_idx = 0

    for result in response.get("results", []):
        title = result.get("title", "").strip()
        url = result.get("url", "")
        content = result.get("content", "")

        product_name = extract_product_name(title)
        if not product_name or product_name.lower() in seen:
            continue
        seen.add(product_name.lower())

        image_url = ""
        if image_idx < len(images):
            image_url = images[image_idx]
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

        for field in request.custom_fields:
            item[f"custom_{field}"] = extract_custom_field(content, field)

        competitors.append(item)
        if len(competitors) >= 8:
            break

    return {
        "category": category,
        "competitors": competitors[:8],
        "summary": response.get("answer", ""),
        "custom_fields": request.custom_fields,
    }


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
    patterns = [
        r"([\d,]+)\s*円",
        r"¥\s*([\d,]+)",
        r"￥\s*([\d,]+)",
    ]
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
