import requests
from datetime import datetime

JSON_URL = "http://141.164.53.195/live/korea-live.json"
OUTPUT1 = "korea.m3u8"    # DIYP 影音
OUTPUT2 = "korea2.m3u8"   # 标准 M3U（支持 php）

# 카테고리 이름 변경 (원래이름 → 새이름)
GROUP_RENAME = {
    "한국-생방송": "한국-생방송1",
    "생방송-테스트": "한국-생방송2",
}

# 카테고리 표시 순서 (이 순서대로, 목록에 없는 건 맨 뒤)
GROUP_ORDER = [
    "한국-생방송1",
    "한국-생방송2",
    "영화",
    "드라마(다시보기)",
    "예능(다시보기)",
    "中国电视",
    "연변방송",
]

def extract_m3u8_only(uris):
    def is_m3u8(u):
        return isinstance(u, str) and ("channel=" in u.lower() or ".m3u8" in u.lower() or u.lower().endswith(".php"))  and "wavve" not in u.lower()
    if isinstance(uris, list):
        for u in uris:
            if is_m3u8(u):
                return u.strip()
    elif isinstance(uris, dict):
        for u in uris.values():
            if is_m3u8(u):
                return u.strip()
    elif isinstance(uris, str):
        if is_m3u8(uris):
            return uris.strip()
    return None

def extract_m3u8_or_php(uris):
    urls = []
    def is_valid(u):
        return isinstance(u, str) and ("channel=" in u.lower() or ".m3u8" in u.lower() or u.lower().endswith(".php"))  and "wavve" not in u.lower()
    if isinstance(uris, list):
        urls = [u.strip() for u in uris if is_valid(u)]
    elif isinstance(uris, dict):
        urls = [u.strip() for u in uris.values() if is_valid(u)]
    elif isinstance(uris, str):
        if is_valid(uris):
            urls = [uris.strip()]
    for u in urls:
        if ".m3u8" in u.lower():
            return u
    if urls:
        return urls[0]
    return None

def run():
    try:
        r = requests.get(JSON_URL, timeout=20)
        r.encoding = "utf-8"
        data = r.json()
    except Exception as e:
        print(f"{datetime.now()} 获取 JSON 失败: {e}")
        return

    items = []
    for item in data:
        name = item.get("name", "").strip()
        uris = item.get("uris")
        group = (item.get("group") or "").strip()
        logo = (item.get("logo") or "").strip()

        if not name or not uris:
            continue

        # 카테고리 이름 변경
        new_group = GROUP_RENAME.get(group, group)

        # "생방송-테스트"(→한국-생방송2) 안의 채널명: "-테스트" → "-2"
        if group == "생방송-테스트" and name.endswith("-테스트"):
            name = name[:-len("-테스트")] + "-2"

        url1 = extract_m3u8_only(uris)
        url2 = extract_m3u8_or_php(uris)

        items.append({
            "group": new_group,
            "logo": logo,
            "name": name,
            "url1": url1,
            "url2": url2,
        })

    # 카테고리 순서대로 정렬 (안정 정렬이라 같은 그룹 내 원래 순서 유지)
    def sort_key(it):
        g = it["group"]
        return GROUP_ORDER.index(g) if g in GROUP_ORDER else len(GROUP_ORDER)
    items.sort(key=sort_key)

    lines1 = ["#EXTM3U"]
    lines2 = ["#EXTM3U"]
    count1 = 0
    count2 = 0

    for it in items:
        name = it["name"]
        group = it["group"]
        logo = it["logo"]

        if it["url1"]:
            lines1.append(f"{name},{it['url1']}")
            count1 += 1

        if it["url2"]:
            attrs = ""
            if logo:
                attrs += f' tvg-logo="{logo}"'
            if group:
                attrs += f' group-title="{group}"'
            lines2.append(f'#EXTINF:-1{attrs},{name}')
            lines2.append(it["url2"])
            count2 += 1

    with open(OUTPUT1, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines1))
    with open(OUTPUT2, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines2))

    print(f"{datetime.now()} DIYP 频道数量: {count1}")
    print(f"{datetime.now()} 标准 M3U 频道数量: {count2}")
    print(f"{datetime.now()} 已生成文件: {OUTPUT1}, {OUTPUT2}")

if __name__ == "__main__":
    run()
