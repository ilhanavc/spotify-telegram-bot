import time
import json
import os
import base64
import requests

# 🔧 AYARLAR

BOT_TOKEN = "8399877149:AAHZbgux7E_-Jpsvrk0TCpD9lbHWQbGmKgQ"  # bot token
CHAT_ID = 746267983  # chat id

SPOTIFY_CLIENT_ID = "1eada413c8154279b74c3c8b8d935dbe"
SPOTIFY_CLIENT_SECRET = "bf6369b921ae40f580d3bd82117abed6"

# Takip etmek istediğin PUBLIC playlist ID'leri
PLAYLIST_IDS = [
    "3qhNJSWFwfNQE8aR5IdAeA",  # 1. playlist
    "4ykazHE5Gl70eMqqWrWmZA",  # 2. playlist (ID'yi Spotify URL'inden tekrar kontrol et)
]

print("DEBUG: Çalışan dosya bu.")
print("DEBUG: PLAYLIST_IDS =", PLAYLIST_IDS)


def get_spotify_token():
    """Spotify API için access token alır (Client Credentials Flow)."""
    auth_str = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}

    resp = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)

    if not resp.ok:
        print("🛑 Spotify token hatası:")
        print("Status:", resp.status_code)
        print("Body:", resp.text)
        resp.raise_for_status()

    return resp.json()["access_token"]


def get_playlist_tracks(access_token, playlist_id):
    """Verilen playlist_id için tüm şarkıları çeker."""
    tracks = []
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"limit": 100}

    while url:
        print(f"Spotify API'ye istek atılıyor: {url}")
        resp = requests.get(url, headers=headers, params=params)

        if not resp.ok:
            print("🛑 Playlist isteğinde hata:")
            print("Status:", resp.status_code)
            print("Body:", resp.text)
            resp.raise_for_status()

        data = resp.json()

        for item in data.get("items", []):
            track = item.get("track")
            if track is None:
                continue
            track_id = track.get("id")
            name = track.get("name", "Bilinmeyen Şarkı")
            artists = ", ".join(a.get("name", "Bilinmeyen Sanatçı") for a in track.get("artists", []))
            added_at = item.get("added_at")
            tracks.append(
                {
                    "id": track_id,
                    "name": name,
                    "artists": artists,
                    "added_at": added_at,
                }
            )

        url = data.get("next")
        params = None  # sonraki sayfa için parametre gerekmez

    return tracks


def send_telegram_message(text):
    """Telegram'a mesaj gönderir."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    resp = requests.post(url, json=payload)

    if not resp.ok:
        print("🛑 Telegram mesaj hatası:")
        print("Status:", resp.status_code)
        print("Body:", resp.text)
        resp.raise_for_status()


def main_loop():
    # Her playlist için ayrı known_tracks set'i ve dosyası
    known = {}

    for pid in PLAYLIST_IDS:
        fname = f"known_{pid}.json"
        if os.path.exists(fname):
            with open(fname, "r", encoding="utf-8") as f:
                known[pid] = set(json.load(f))
        else:
            known[pid] = set()

    print("Takip edilen playlist sayısı:", len(PLAYLIST_IDS))

    while True:
        try:
            token = get_spotify_token()

            for pid in PLAYLIST_IDS:
                print(f"\n🎧 Playlist kontrol ediliyor: {pid}")

                tracks = get_playlist_tracks(token, pid)
                print(f"Playlist'ten gelen toplam şarkı sayısı: {len(tracks)}")

                new_tracks = [t for t in tracks if t["id"] not in known[pid] and t["id"] is not None]

                if new_tracks:
                    new_tracks.reverse()  # en eski yeni şarkıdan başla
                    for t in new_tracks:
                        msg = (
                            "🎵 Yeni şarkı eklendi!\n"
                            f"Playlist: https://open.spotify.com/playlist/{pid}\n"
                            f"Şarkı: {t['name']}\n"
                            f"Sanatçı(lar): {t['artists']}"
                        )
                        print("Telegram'a mesaj gönderiliyor:", msg)
                        send_telegram_message(msg)
                        known[pid].add(t["id"])

                    # bu playlist için kayıt dosyasını güncelle
                    fname = f"known_{pid}.json"
                    with open(fname, "w", encoding="utf-8") as f:
                        json.dump(list(known[pid]), f, ensure_ascii=False, indent=2)
                else:
                    print("Yeni şarkı yok.")

        except Exception as e:
            print("Hata:", e)

        time.sleep(60)  # her 60 saniyede bir tüm playlist'leri kontrol et


if __name__ == "__main__":
    main_loop()
