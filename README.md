# Friendship Meter ☕✨

A soft, casual English-Marathi friendship quiz designed as a delightful mobile-first web game between friends who enjoy chai, late-night calls, Marathi expressions, friendly teasing, memes, and spontaneous plans.

---

## 🎨 Visual Identity
- **Cream Background:** `#FFF8F0`
- **Soft Blush Pink:** `#F6DCE5`
- **Muted Lavender:** `#DCD5F7`
- **Butter Yellow Accents:** `#F6E8A8`
- **Deep Plum Text:** `#65536B`
- **Typefaces:** [Quicksand](https://fonts.google.com/specimen/Quicksand) (rounded sans-serif) & [Patrick Hand](https://fonts.google.com/specimen/Patrick+Hand) (handwritten notes).

---

## 📱 Screen-by-Screen Flow

1. **Welcome (`Friendship Meter`)**
   - Natural English-Marathi introduction with nickname input (`Tula kay mhanto apan?`).
2. **8-Question Quiz**
   - One question per screen with large touch cards, progress bar, back navigation, and answer persistence:
     1. *What's your ideal plan?* (Chai ani gappa, Long drive, random songs, Gharich basu, please, Plan karu, cancel karu)
     2. *Someone says "kahi nahi" — what does it mean?* (Literally kahi nahi, Bharpur kahi tari aahe, Mood off aahe, clearly, Depends on the person)
     3. *A 10-minute call becomes 2 hours. Why?* (Gossip cha stock sampat nahi, Ek topic varun dusra, Comfortable silence pan chalta, Arey, time kasa gela kalalach nahi)
     4. *Best way to fix a bad mood?* (Chaha ani kahi tari khaayla, Ek mast rant session, Memes pathav, lecture nako, Thoda time ani peace)
     5. *"Kay challay?" usually means…* (Genuine update pahije, Bore zhaloy, bol na, Kahi gossip aahe ka?, Just checking in)
     6. *What's your texting personality?* (Instant reply gang, Reply in my head, forget IRL, Voice notes supremacy, Depends on my mood yaar)
     7. *Last-minute plan: "Chal, baher jau."* (Location pathav, I'm ready, Kuthay? Kiti vajta? Kon yenar?, Aai la vicharun sangto, Udyala jau, aaj blanket day)
     8. *When someone teases you, you…* (Full comeback ready aahe, Laugh karto, mag revenge, Pretend ki farak padat nahi, Teasing back is my love language)
3. **Initial Friendship Score**
   - Deterministic score out of 100 with animated progress bar and result bands:
     - `0–39`: *Ajun olakh vhaychi aahe*
     - `40–59`: *Chai-pani acquaintances*
     - `60–79`: *Gappa gang material*
     - `80–94`: *Gappa Champion*
     - `95–100`: *Full-time bakbak partner*
   - Explains clearly that this is an initial score before distance calculation.
4. **Distance Challenge**
   - Heading: *"Okay waittt… ek important question aahe! 📍"*
   - Copy: *"Apan quiz tar complete kela… but actually tu Prajwal pasun kiti lamb aahe?"*
   - Cute graphic with two location pins (**You** and **Prajwal**) connected by a dotted line.
   - Transparent consent with button: **"Chal, distance calculate karu ♡"**.
   - Server calculates straight-line great-circle distance via Haversine formula against configured reference coordinates (`PRAJWAL_LAT: 13.103691`, `PRAJWAL_LON: 77.570392`) without leaking them to the public frontend.
   - Displayed distance in km (or metres for short distance) with playful captions (*"Arey, almost same area!"*, *"Thoda travel tar banta hai."*, *"Bakbak sathi kilometres don't matter."*).
5. **Final Friendship Score: Quiz + Distance**
   - Formula: `round((Quiz score × 0.80) + (Distance score × 0.20))`
   - Distance points scale: 0-5 km: 100 pts, 5-25 km: 80 pts, 25-100 km: 60 pts, 100-300 km: 40 pts, >300 km: 20 pts.
   - Breakdown cards showing 80% quiz contribution and 20% distance contribution.
6. **Combined Vacation Recommendation + Location Challenge (Single Screen)**
   - Heading: *"Okayyy, where should your vibe take you? 🌍"*
   - Postcard getaway matched to answers (Lonavala & Khandala, Alibaug Beach, FC Road Pune, Tamhini Ghat).
   - Integrated card: *"One tiny challenge before we plan your getaway 📍"*
   - Checkbox: explicit agreement to share location with the app creator.
   - Button: **"Go for it♡"**
   - Upon confirmed server transmission: displays victory banner (*"hehe, challenge completed ♡"*, *"Bragging rights: acquired."*), measured coordinates, reported accuracy in metres, map link, and copyable summary dossier.

---

## 🔐 Administrator Dashboard

Visit **`/admin`** to log in with administrator credentials:
- **Default Username:** `admin`
- **Default Password:** `prajwal@friendship2026`

View all game sessions, quiz scores, distances, final scores, and consented GPS transmissions in real time.

---

## 🚀 Running the App & Verification

```bash
cd /Users/prajwalkolaki/.gemini/antigravity/scratch/tiny-friend-game

# Run unit and integration tests
python3 test_scoring_and_distance.py
python3 test_server_api.py

# Launch the server
python3 server.py
```
Open **`http://localhost:8000`** in your browser.
