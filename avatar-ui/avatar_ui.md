
# Avatar Assembly UI & Interchangeable Pack — Full Tech Spec

> **Scope:** A browser UI where you drop a PSD; it auto-extracts slices, highlights unmapped ones, lets you drag→drop to standard **Slots**, and exports a **ZIP bundle** that includes **all slices with their original PSD paths** plus a **canonical avatar manifest** so you can later swap clothes/hair across projects.

---

## 1) Goals
- Zero-install, **client-side** tool (no server) to assemble 2D avatars from PSDs.
- Define a **portable avatar standard** (Parts → Slots) that different PSDs can target.
- Export a **ZIP bundle** that contains:
  - Runtime-ready `avatar.json` + (optional) `graph.json`
  - **All slices twice**: canonical (by Slot) and raw (by PSD path)
  - A **wardrobe catalog** for interchangeable items (hair/clothes/accessories)
  - **Rules** (`PCS_RULES.yaml`) learned from manual mapping for future PSDs
- Enable later reuse in other apps (web, game engines) to **swap items** cleanly.

---

## 2) Vocabulary (recap)
- **Layer (PSD)**: raw element inside Photoshop.
- **Slice**: rasterized cutout of a Layer/Group (exported PNG + rect).
- **Slot**: semantic placeholder in the character (e.g., `Mouth.viseme.AI`).
- **Part**: grouping of slots (e.g., `EyeL` with `open|closed|half` states).
- **Item**: a slice (or set of slices) that can be **equipped** (e.g., a Top, a Hair style).
- **Bundle**: the exported ZIP that holds manifests + slices + rules + previews.

---

## 3) Canonical Avatar Standard (Parts & Slots)

### Parts
1. **Body** — `torso`, `arms`, `legs`
2. **Head** — `base`, `neck`
3. **Hair** — `back`, `mid`, `front`, `accessory`
4. **Eyes** — `EyeL.state:(open|half|closed)`, `EyeR.state:(open|half|closed)`, `IrisL`, `IrisR`, `BrowL.shape:(neutral|up|down|angry|sad)`, `BrowR.shape:(neutral|up|down|angry|sad)`
5. **Mouth** — `viseme:(REST|AI|E|U|O|FV|L|WQ|MBP|SIL)`, `emotion:(neutral|smile|frown|angry|sad|joy)`
6. **Nose** — `base`, `shadow`
7. **Cheek** — `blush`, `shadow`
8. **Accessories** — `glasses`, `earrings`, `hats`, `masks`
9. **FX** — `sparkles`, `highlights`

> You can extend with custom Parts/Slots; unknown keys are preserved.

---

## 4) Coordinate System & Placement

- **Canvas Space:** All slices are positioned in a shared, immutable **avatar coordinate space** (e.g., 1024×1024). The PSD is rasterized into this space; each slice stores: `x,y,w,h`.
- **Anchors (attachment points):** Standard named points (pixel coords) defined in `avatar.json`:
  - `headPivot`, `neckBase`, `earL`, `earR`, `browL`, `browR`, `mouthCenter`, `noseTip`, `shoulderL`, `shoulderR`, `headTop`.
- **Transforms:** For simple 2D, we store only translation (x,y). Optional: `scaleX/Y`, `rotation` for item tweaks.
- **Z-Order (draw order):** Global canonical order (bottom→top):

  1. Body
  2. Head(base)
  3. Hair(back)
  4. Neck/Ears
  5. Eyes (whites/irises)
  6. Brows
  7. Mouth
  8. Nose
  9. Cheek
  10. Hair(front)
  11. Accessories
  12. FX

  Items can request small **z-offsets** (`+/-2`) via item metadata; engine clamps to safe ranges.

- **Masks (optional):** A Part may define an occlusion mask (e.g., bangs masking brows). Masks are simple alpha sprites declared per Part.

---

## 5) Interchangeability Model (Wardrobe)

- **Item Types:** `hair`, `top`, `bottom`, `outerwear`, `shoes`, `glasses`, `earrings`, `hat`, `mask`, `fx`…
- **Exclusive Groups:** Only one active per group, e.g., one `hair` style, one `top`. Some types pair (hair has `front` + `back` that must match the same SKU).
- **Fit Box:** Each avatar declares a **fitBox** per type (rect in canvas space). Items declare the **target fitBox** they’re authored for (by `rigId` or numeric rect). If `rigId` matches, it’s guaranteed to fit; otherwise the UI can warn or scale to fit.
- **Compatibility Token:** `rigId` (string). Items made for the same `rigId` are drop-in compatible across avatars in the same “family”.

---

## 6) Exported ZIP Bundle — Structure (v1)

```
<AvatarName>_bundle_v1.zip
├─ manifest.json                # meta + versions + entry points
├─ avatar.json                  # canonical slots, slices, draw order, anchors
├─ graph.json                   # (optional) expression graph
├─ psd-paths.json               # raw PSD tree → slice IDs & canonical slots
├─ rules/
│   └─ PCS_RULES.yaml           # learned aliases/regex for future PSDs
├─ slices/
│   ├─ canon/                   # canonical slices by Slot
│   │   ├─ Hair/front.png
│   │   ├─ Hair/back.png
│   │   ├─ Mouth/viseme/AI.png
│   │   └─ ... (mirrors slot keys as dirs)
│   └─ raw/                     # original PSD path layout for auditing/swaps
│       ├─ Face/Mouth/A.png
│       ├─ Hair/Front/Bangs 1.png
│       └─ ...
├─ wardrobe/                    # interchangeable items packaged as mini-bundles
│   ├─ hair/
│   │   ├─ short_bob/
│   │   │   ├─ item.json        # metadata, slots it fills, z-offsets, fitBox
│   │   │   ├─ front.png
│   │   │   └─ back.png
│   │   └─ long_twin_tails/...
│   ├─ tops/
│   │   └─ hoodie_blue/
│   │       ├─ item.json
│   │       └─ torso_overlay.png
│   └─ ...
├─ previews/
│   ├─ avatar.png               # assembled preview
│   ├─ hair_short_bob.png
│   └─ hoodie_blue.png
└─ README.txt
```

### 6.1 `manifest.json` (example)
```json
{
  "name": "Female Sprite by Sutemo",
  "version": "1.0.0",
  "schema": { "avatar": "1.0.0", "bundle": "1.0.0" },
  "entry": { "avatar": "avatar.json", "graph": "graph.json" },
  "rigId": "anime-1024-headA-v1",
  "fitBoxes": {
    "hair": { "x": 280, "y": 40, "w": 460, "h": 520 },
    "top":  { "x": 240, "y": 380, "w": 520, "h": 420 }
  },
  "hashes": { "avatar.json": "sha256-...", "slices/canon/Hair/front.png": "sha256-..." }
}
```

### 6.2 `avatar.json` (key fields)
```json
{
  "meta": { "generator": "psd-ce@1.0.0", "rigId": "anime-1024-headA-v1" },
  "images": {
    "atlas": "atlas.png",
    "slices": {
      "Hair/front": { "x": 620, "y": 0, "w": 280, "h": 260, "id": "slc_ha_f_01" },
      "Mouth/viseme/AI": { "x": 320, "y": 220, "w": 40, "h": 22, "id": "slc_m_ai_01" }
    }
  },
  "drawOrder": [
    "Body/*",
    "Head/*",
    "Hair/back",
    "Eyes/*",
    "Brows/*",
    "Mouth/*",
    "Nose/*",
    "Cheek/*",
    "Hair/front",
    "Accessories/*",
    "FX/*"
  ],
  "anchors": {
    "headPivot": { "x": 512, "y": 256 },
    "mouthCenter": { "x": 520, "y": 320 }
  }
}
```

### 6.3 `psd-paths.json` (maps raw → canonical)
```json
{
  "layers": [
    {
      "psdPath": "Face/Mouth/A",
      "sliceId": "slc_m_ai_01",
      "canonical": "Mouth/viseme/AI"
    },
    {
      "psdPath": "Hair/Front/Bangs 1",
      "sliceId": "slc_ha_f_01",
      "canonical": "Hair/front"
    }
  ]
}
```

### 6.4 `wardrobe/<type>/<sku>/item.json`
```json
{
  "type": "hair",
  "sku": "short_bob",
  "rigId": "anime-1024-headA-v1",
  "fills": ["Hair/front", "Hair/back"],
  "zOffsets": { "Hair/front": 0, "Hair/back": 0 },
  "fitBox": { "x": 280, "y": 40, "w": 460, "h": 520 },
  "slices": {
    "Hair/front": "front.png",
    "Hair/back": "back.png"
  },
  "variants": [
    { "name": "brown", "tint": "#6a4b3c" },
    { "name": "black", "tint": "#1a1a1a" }
  ],
  "tags": ["bob", "short", "cute"],
  "license": "CC-BY-4.0"
}
```

---

## 7) UI Features (focused)

### 7.1 Landing / FileBar
- **Drop PSD** → parse → slice → auto-map using rules; produce atlas + draft `avatar.json`.
- **Open Bundle** → load an existing ZIP to edit/fix.

### 7.2 Unmapped Slices Panel
- Shows thumbnails of slices that didn’t map.
- Search/filter; multi-select.
- Drag to **Slot Palette** (Parts→Slots) to assign.
- On drop:
  - Update `avatar.json.images.slices` key to canonical.
  - Copy the PNG into `slices/canon/<SlotKey>.png`.
  - Add a learned alias to pending `PCS_RULES.yaml`.
  - Append an entry to `psd-paths.json` for audit.

### 7.3 Avatar Canvas (PixiJS)
- Renders slices in **canonical draw order**.
- Hover highlight; select to open **Slot Inspector**.
- Toggle visibility per Part to debug overlaps.
- (Optional) show anchor points & fitBoxes overlays.

### 7.4 Slot Palette & Inspector
- Palette renders from a **Slot Palette JSON** (see §8).
- Inspector shows current slice for a Slot; actions: Replace, Remove, Nudge Z (±2), Tint (write to item.json if in wardrobe context).

### 7.5 Wardrobe Tab
- Create new **Item** from selected slices (e.g., convert current hair into `wardrobe/hair/<sku>`).
- Item wizard asks: `type`, `sku`, `fills[]`, `fitBox`, `variants` (tints).
- Save writes `item.json` + images under the wardrobe path and **removes** those slices from `avatar.json` if desired (equipping becomes a runtime concern).

### 7.6 Export
- **Export ZIP** with structure in §6.
- Options: include atlas; include raw slices; compress level.
- Validate: essentials (Eyes L/R open/closed, Mouth REST + ≥5 visemes), `rigId`, anchors present.

---

## 8) Slot Palette Definition (drives UI)

`slot_palette.json` shipped in the app to avoid hardcoding:

```json
{
  "Body": { "torso": {}, "arms": {}, "legs": {} },
  "Head": { "base": {}, "neck": {} },
  "Hair": { "back": {}, "mid": {}, "front": {}, "accessory": {} },
  "Eyes": {
    "EyeL": { "state": ["open","half","closed"] },
    "EyeR": { "state": ["open","half","closed"] },
    "IrisL": {}, "IrisR": {},
    "BrowL": { "shape": ["neutral","up","down","angry","sad"] },
    "BrowR": { "shape": ["neutral","up","down","angry","sad"] }
  },
  "Mouth": {
    "viseme": ["REST","AI","E","U","O","FV","L","WQ","MBP","SIL"],
    "emotion": ["neutral","smile","frown","angry","sad","joy"]
  },
  "Nose": { "base": {}, "shadow": {} },
  "Cheek": { "blush": {}, "shadow": {} },
  "Accessories": { "glasses": {}, "earrings": {}, "hats": {}, "masks": {} },
  "FX": { "sparkles": {}, "highlights": {} }
}
```

---

## 9) File Formats & Schemas (essentials)

### 9.1 `avatar.json` (min required)
- `meta.generator`, `meta.rigId`
- `images.atlas` (or allow per-slice files only)
- `images.slices[slotKey] = {x,y,w,h,id}`
- `drawOrder[]` (supports wildcards like `Body/*`)
- `anchors{ name: {x,y} }`

### 9.2 `psd-paths.json`
- Array of `{ psdPath, sliceId, canonical }`

### 9.3 `PCS_RULES.yaml` (example)
```yaml
aliases:
  - match: "(?i)mouth[_ -]?a(i)?"
    map: { group: Mouth, slot: "Mouth/viseme/AI" }
  - match: "(?i)hair[/ _-]?front[/ _-]?bangs?"
    map: { group: Hair, slot: "Hair/front" }
```

### 9.4 `item.json`
- `type`, `sku`, `rigId`, `fills[]`, `fitBox`, `slices{slotKey: file}`
- Optional: `zOffsets{slotKey: int}`, `variants[]`, `tags[]`, `license`

---

## 10) Implementation Plan (UI, 3–4 days)

**Day 1** — Scaffolding & Ingest
- Vite + React + TypeScript + PixiJS; Ajv for schema validation.
- PSD loader (psd.js) → rasterize slices → initial atlas (or direct sprite batch).
- Auto-map with existing rules; produce draft `avatar.json`, `psd-paths.json`.

**Day 2** — Mapping UX
- Unmapped panel w/ thumbnails; Slot Palette from `slot_palette.json`.
- Drag→drop mapping updates in-memory docs + preview.
- Generate pending `PCS_RULES.yaml` entries on every mapping.

**Day 3** — Exporter
- ZIP writer (JSZip): emit structure in §6.
- Create `manifest.json`, copy slices to `/slices/raw` and `/slices/canon`.
- Generate `previews/*` via snapshotting Pixi canvas.

**Day 4 (optional)** — Wardrobe
- Item wizard + writer for `wardrobe/<type>/<sku>`.
- FitBox overlay and rigId selection.
- Equip/unequip preview (runtime simulation).

---

## 11) Runtime Notes (for other projects)
- Load `manifest.json` → `avatar.json` → drawOrder + slices.
- To **swap items**, load `wardrobe/.../item.json`, check `rigId`/fitBox, and replace the corresponding Slot sprites.
- Respect `zOffsets` and anchors; clamp to safe ranges.

---

## 12) Quality & Validation
- Ensure **replayable builds**: include file hashes in `manifest.json`.
- Schema-check `avatar.json`, `item.json` at export time (Ajv).
- Visual diff: generate `previews/avatar.png` before and after mapping.

---

## 13) Security & Privacy
- Entirely local; no network calls.
- Ask permission only for File System Access API; fallback to download blobs.

---

## 14) License & Attribution
- Record `license` fields on items and avatar; copy into `README.txt`.
- If PSD art needs attribution, embed it into `manifest.json.credits`.
