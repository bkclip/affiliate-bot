import csv, requests, os, time

# 1. Baca daftar produk
with open("products.csv") as f:
    products = list(csv.DictReader(f))

for p in products:
    # 2. Generate script + caption pakai LLM API
    script_resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        json={"model": "gpt-4o-mini", "messages": [
            {"role": "user", "content": f"Buatkan script video 30 detik + caption + hashtag untuk produk: {p['nama']}"}
        ]}
    ).json()
    script_text = script_resp["choices"][0]["message"]["content"]

    # 3. Kirim ke video render API (JSON2Video)
    video_resp = requests.post(
        "https://api.json2video.com/v2/movies",
        headers={"x-api-key": os.environ["JSON2VIDEO_API_KEY"]},
        json={
            "resolution": "instagram-story",
            "scenes": [{"elements": [
                {"type": "image", "src": p["foto_url"]},
                {"type": "text", "text": script_text}
            ]}]
        }
    ).json()

    # 4. Simpan hasil (URL video + caption) — misal ke file/artifact repo
    with open("output.txt", "a") as out:
        out.write(f"{p['nama']} | {video_resp.get('id')} | {script_text}\n")
