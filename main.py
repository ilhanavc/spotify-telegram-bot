import time
import json
import os
import base64
import requests

# ---------------------------------------
# AYARLAR (BUNLARI DOLDUR)
# ---------------------------------------

BOT_TOKEN = "8399877149:AAHZbgux7E_-Jpsvrk0TCpD9lbHWQbGmKgQ"
CHAT_ID = 746267983

SPOTIFY_CLIENT_ID = "1eada413c8154279b74c3c8b8d935dbe"
SPOTIFY_CLIENT_SECRET = "bf6369b921ae40f580d3bd82117abed6"

# Takip edilen playlistler
PLAYLIST_IDS = [
    "3qhNJSWFwfNQE8aR5IdAeA",      # Playlist 1
    "4ykazHE5Gl70eMqqWrWmZA"       # Playlist 2
]


# ---------------------------------------
# TOKEN ALMA
# ---------------------------------------
def get_spotify_token():
    auth_str = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = { "grant_type": "client_credentials" }

    resp = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    resp.raise_for_status()
    return resp.json()["access_token"]


# ---------------------------------------
# PLAYLIST ŞARKILARINI ÇEKME
# ---------------------------------------
def get_playlist_tracks(pid, token):
    url = f"https://api.spotify.com/v1/playlists/{pid}/tracks"
    headers = { "Authorization": f"Bearer {token}" }
    params = { "limit": 100 }

    tracks = []

    while url:
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("items", []):
            track = item.get("track")
            if not track:
                continue

            tid = track.get("id")
            name = track.get("name", "Unknown Track")
            artists = ", ".join(a.get("name", "Unknown Artist") for a in track.get("artists", []))
            added_at = item.get("added_at")

            tracks.append({
                "id": tid,
                "name": name,
                "artists": artists,
                "added_at": added_at
            })

        url = data.get("next")
        params = None

    return tracks


# ---------------------------------------
# TELEGRAM MESAJ GÖNDERME
# ---------------------------------------
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = { "chat_id": CHAT_ID, "text": text }

    resp = requests.post(url, json=payload)
    resp.raise_for_status()


# ---------------------------------------
# MAIN LOOP
# ---------------------------------------
def main():
    known = {}

    # Her playlist için ayrı state dosyası
    for pid in PLAYLIST_IDS:
        fname = f"known_{pid}.json"
        if os.path.exists(fname):
            with open(fname, "r") as f:
                known[pid] = set(json.load(f))
        else:
            known[pid] = set()

    print("Bot Render üzerinde çalışıyor...")

    while True:
        try:
            token = get_spotify_token()

            for pid in PLAYLIST_IDS:
                print(f"\nKontrol ediliyor → {pid}")
                tracks = get_playlist_tracks(pid, token)

                new_tracks = [t for t in tracks if t["id"] not in known[pid]]

                if new_tracks:
                    new_tracks.reverse()

                    for t in new_tracks:
                        msg = (
                            "🎵 Yeni şarkı eklendi!\n"
                            f"Playlist: https://open.spotify.com/playlist/{pid}\n"
                            f"Şarkı: {t['name']}\n"
                            f"Sanatçı: {t['artists']}"
                        )
                        send_telegram_message(msg)
                        known[pid].add(t["id"])

                    # Kaydet
                    with open(f"known_{pid}.json", "w") as f:
                        json.dump(list(known[pid]), f, indent=2)

                else:
                    print("Yeni şarkı yok.")

        except Exception as e:
            print("HATA:", e)

        time.sleep(60)  # 60 saniyede bir kontrol


if __name__ == "__main__":
    main()
