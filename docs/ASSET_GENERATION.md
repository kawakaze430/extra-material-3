# Original illustration prompts and production history

These are the prompts used to create the pilot's artwork with the OpenAI image-generation tool available in the Codex session. The tool did not report an exact model version, seed, or sampling configuration. No fine-tuning was performed. Repeating a prompt will not reproduce identical pixels: use the checked-in PNGs to reproduce the pilot.

Only the character artwork was generated as images. The moving video was assembled frame by frame by `studio/render.py`; an AI video model was not used.

## 1. Cafe background

Output: [`studio/assets/cafe.png`](../studio/assets/cafe.png), 1672 × 941, opaque RGB. The request used `transparent_background=false` and no reference image.

```text
Create a polished professional 2D animated-film BACKGROUND ONLY for a cozy modern neighborhood cafe, wide cinematic 16:9 composition, warm honey sunlight, teal and sage cabinetry, terracotta cups, espresso machine, beautiful painterly texture with clean elegant cartoon shapes, tasteful soft lighting and rich color grading. NO PEOPLE, NO CHARACTERS, NO TEXT, NO LOGOS. Eye-level medium-wide camera. Main counter is a slim horizontal oak surface at 75 percent down the canvas spanning full width, leaving foreground bottom quarter dark warm wood. Behind counter on right an espresso machine and shelves; left has windows, leafy plants and cozy cafe depth. Main middle area behind future characters should be relatively quiet simple warm cream and muted teal. Composition reserves space for a waist-up woman in left third and waist-up barista man in right third; neither exists in this image. Top left quiet space for episode title. Not photorealistic; sophisticated hand-drawn animation production background with cohesive cinematic art direction. Render high resolution.
```

## 2. Character sheets

Both character calls used the background above as their style reference, with `transparent_background=true`. The full prompt for each character was the common prompt immediately followed by its character-specific suffix.

Common prompt:

```text
Create an animation SPRITE SHEET on a fully TRANSPARENT background, 4 equal columns x 2 equal rows, exactly eight evenly spaced isolated WAIST-UP character drawings. No panels, no text, no labels, no background, no shadows outside character. Each of the 8 cells contains the SAME character at IDENTICAL SIZE, torso/head positions and camera angle. Leave transparent gutter around every drawing. Keep all hair, head, elbows and hands fully inside each cell. Sophisticated hand-painted 2D animation art, clean expressive features, soft shaded volume and warm rim light, matching the supplied cafe background's art style. Critical: frame-to-frame consistent face, clothing, body proportions and alignment. Eyes look toward the other person, not the viewer. Top row cells left to right: 1 relaxed attentive pose with CLOSED smiling mouth; 2 EXACT SAME POSE with small speaking mouth; 3 EXACT SAME POSE with open speaking mouth and visible tongue; 4 EXACT SAME POSE with closed mouth and closed eyes for blink. Bottom row cells left to right: 5 friendly conversational gesture with one palm gently raised, CLOSED mouth; 6 EXACT SAME GESTURE with small speaking mouth; 7 EXACT SAME GESTURE with open speaking mouth; 8 EXACT SAME GESTURE with closed mouth and eyes closed for blink. All poses should be natural, attractive, subtle and expressive. No duplicate arms or fingers. Center character on identical vertical axis in all cells. The supplied image is STYLE REFERENCE ONLY. Do not reproduce the background.
```

Maya suffix:

```text
 Character: MAYA, original friendly adult woman about 28, warm medium brown skin, beautiful dark brown shoulder-length wavy hair with a small golden hair clip, warm brown eyes, coral cardigan over a cream blouse, small gold earrings, modern expressive animated-film character design. Three-quarter view turned slightly toward image RIGHT. Torso cropped just below waist, arms/hands visible. Gesture hand is toward the right, open palm as she orders coffee.
```

Output: [`studio/assets/maya.png`](../studio/assets/maya.png), 1774 × 887, RGBA.

Leo suffix:

```text
 Character: LEO, original friendly adult man about 30, light olive skin, short thick slightly curly dark brown hair, clean shaven, expressive brown eyes and eyebrows, rolled sleeve cream shirt under a deep teal barista apron with brass strap fasteners, modern expressive animated-film character design. Three-quarter view turned slightly toward image LEFT. Torso cropped just below waist, arms/hands visible. Gesture hand is toward left, open palm as he welcomes a customer.
```

The first Leo output had residual background opacity despite the transparency request. It is preserved as [`studio/assets/source/leo-before-transparency.png`](../studio/assets/source/leo-before-transparency.png) for provenance; the renderer does not use it.

## 3. Leo transparency correction

The original Leo sheet was supplied as the reference image; `transparent_background=true` was requested again.

```text
Remove the white/paper background completely to alpha zero transparency from this existing 4 columns by 2 rows eight-frame sprite sheet. Preserve all eight character drawings, identical positions, identical sizes, original grid dimensions, colors, faces, hands, clothing, shading and details exactly. Do not redesign or rearrange. The spaces around and between all characters must be fully transparent, no residual white haze, no checkerboard artwork. Output PNG with genuine clear alpha outside all character silhouettes.
```

Final output: [`studio/assets/leo.png`](../studio/assets/leo.png), 1774 × 887, RGBA. The final Maya and Leo sheets have alpha values spanning 0–255.

## Frame contract

The renderer splits each sheet into four columns and two rows, preserving each cell's canvas and resizing it to 444 × 444 pixels. Indices are zero based:

| Index | Body pose | Face |
| --- | --- | --- |
| 0 | Resting hands | Closed mouth |
| 1 | Resting hands | Small speaking mouth |
| 2 | Resting hands | Wide speaking mouth |
| 3 | Resting hands | Blink, closed mouth |
| 4 | Raised palm | Closed mouth |
| 5 | Raised palm | Small speaking mouth |
| 6 | Raised palm | Wide speaking mouth |
| 7 | Raised palm | Blink, closed mouth |

The explicit **WAIST-UP** instructions above explain the missing lower body. No hidden full-body drawing, editable limb layers, skeleton, mesh, or trained character model exists in these images. New full-body assets and animation controls would have to be created; changing a crop cannot reveal legs that were never generated.
