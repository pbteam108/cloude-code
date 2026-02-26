from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from tavily import TavilyClient
from dotenv import load_dotenv
import os
import re

load_dotenv()

app = FastAPI()
client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


class SearchRequest(BaseModel):
    category: str


@app.post("/api/search")
async def search_competitors(request: SearchRequest):
    category = request.category.strip()
    if not category:
        raise HTTPException(status_code=400, detail="カテゴリーを入力してください")

    query = f"{category} 競合製品 サービス一覧 比較"

    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=10,
        include_answer=True,
    )

    competitors = []
    seen = set()

    for result in response.get("results", []):
        title = result.get("title", "").strip()
        url = result.get("url", "")
        content = result.get("content", "")

        # タイトルから製品名を抽出（重複除去）
        product_name = extract_product_name(title)
        if product_name and product_name.lower() not in seen:
            seen.add(product_name.lower())
            competitors.append({
                "name": product_name,
                "description": content[:120] + "..." if len(content) > 120 else content,
                "url": url,
            })

    return {
        "category": category,
        "competitors": competitors[:8],
        "summary": response.get("answer", ""),
    }


def extract_product_name(title: str) -> str:
    # 「〜 vs 〜」「〜 比較」などのパターンから製品名を取り出す
    title = re.sub(r"[\|｜\-–—].*$", "", title).strip()
    title = re.sub(r"(の比較|比較|レビュー|とは|料金|評判).*$", "", title).strip()
    return title[:40] if title else ""


app.mount("/", StaticFiles(directory="static", html=True), name="static")
