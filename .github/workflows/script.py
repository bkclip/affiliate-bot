import csv
import os
import time
import json
import requests

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
JSON2VIDEO_API_KEY = os.environ["JSON2VIDEO_API_KEY"]

def generate_script_caption(nama_produk):
    prompt = (
        f"Buatkan script video promosi 30 detik untuk produk: {nama_produk}. "
        "Gaya santai, hook di 3 detik pertama, ada call-to-action di akhir. "
        "Sertakan juga caption TikTok yang menarik dan 5 hashtag relevan. "
        "Balas HANYA dalam format JSON valid seperti ini: "
        '{"script": "...", "caption": "...", "hashtags": ["...", "..."]}'
    )
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8
        },
        timeout=60
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    # bersihkan kalau ada ```json wrapper
    content = content.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(content)

def render_video(foto_url, caption):
    payload = {
        "resolution": "instagram-story",
        "scenes": [
            {
                "elements": [
                    {"type": "image", "src": foto_url},
                    {"type": "text", "text": caption,
                     "settings": {"font-size": "48px", "position": "bottom"}}
                ]
            }
        ]
    }
    resp = requests.post(
        "https://api.json2video.com/v2/movies",
        headers={"x-api-key": JSON2VIDEO_API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=60
    )
    resp.raise_for_status()
    job_id = resp.json()["project"]

    # polling status render sampai selesai
    for _ in range(30):
        time.sleep(10)
        status_resp = requests.get(
            f"https://api.json2video.com/v2/movies?project={job_id}",
            headers={"x-api-key": JSON2VIDEO_API_KEY},
            timeout=30
        ).json()
        if status_resp.get("movie", {}).get("status") == "done":
            return status_resp["movie"]["url"]
    return None

def main():
    rows = []
    with open("products.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    results = []
    for row in rows:
        if row["status"].strip().lower() != "pending":
            continue

        print(f"Memproses: {row['nama_produk']}")
        try:
            data = generate_script_caption(row["nama_produk"])
            video_url = render_video(row["foto_url"], data["caption"])

            results.append({
                "produk": row["nama_produk"],
                "caption": data["caption"],
                "hashtags": " ".join(data["hashtags"]),
                "video_url": video_url,
                "link_affiliate": row["link_affiliate"]
            })
            row["status"] = "done"
        except Exception as e:
            print(f"Gagal proses {row['nama_produk']}: {e}")
            row["status"] = "error"

    # update ulang CSV supaya produk yang sudah diproses tidak diulang
    with open("products.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["nama_produk","foto_url","link_affiliate","status"])
        writer.writeheader()
        writer.writerows(rows)

    # simpan hasil ke file output supaya bisa dicek
    with open("output/hasil_terbaru.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Selesai. {len(results)} video diproses.")

if __name__ == "__main__":
    main()
