# Mobile Album Upload

Create and upload albums directly from your iPhone using two iOS Shortcuts.

## Prerequisites

1.  **GitHub Account**
2.  **Fine-grained Personal Access Token (Recommended)**
    *   Go to [Developer Settings > Personal access tokens > Fine-grained tokens](https://github.com/settings/tokens?type=beta).
    *   **Generate new token**.
    *   **Repository access**: Select `ignaciojimenezpi.github.io`.
    *   **Permissions**: `Contents` -> **Read and write**.
    *   **Save the token**.

## Workflow

Two shortcuts work together:

1.  **Copy Cover Name** — run this first on the single photo you want as the album cover. It copies the image filename to the clipboard.
2.  **Upload Album** — run this on all photos for the album. It reads the cover name from the clipboard and uploads everything.

**Usage order**:
1.  Open the cover photo in Photos → Share → **Copy Cover Name**.
2.  Go back, select all album photos → Share → **Upload Album**.

---

## Shortcut 1: Copy Cover Name

A minimal shortcut that copies the selected image's filename stem to the clipboard.

*   **Name**: `Copy Cover Name`
*   Open **Shortcut Details** → enable **Show in Share Sheet** → limit to **Images**.

Add these two actions:

1.  **Get Details of Images**
    *   Detail: **Name**
    *   Image: **Shortcut Input**
2.  **Copy to Clipboard**
    *   Content: result of previous action

That's it. Running this on a photo puts `IMG_1234` (or equivalent) on the clipboard, ready for the upload shortcut to consume.

---

## Shortcut 2: Upload Album

### Variables Reference

| Variable | Where set | What it holds |
|---|---|---|
| `Token` | Step 2 | GitHub PAT |
| `User` | Step 2 | `ignaciojimenezpi` |
| `Repo` | Step 2 | `ignaciojimenezpi.github.io` |
| `AlbumTitle` | Step 3 | e.g. `Summer in Barcelona` |
| `AlbumDate` | Step 3 | e.g. `2025-07-01` |
| `AlbumDescription` | Step 3 | Free text |
| `AlbumID` | Step 4 | e.g. `summer-in-barcelona` |
| `CoverImageName` | Step 5 | Read from clipboard (set by Copy Cover Name) |
| `ImageStem` | Inside loop | Current image filename stem, e.g. `IMG_1234` |
| `EncodedImage` | Inside loop | Base64 of current image |

### 1. Create Shortcut

*   **Name**: `Upload Album`
*   Open **Shortcut Details** → enable **Show in Share Sheet** → limit to **Images**.

### 2. Set Constants

Add three **Text** actions and save each to a variable:

| Action | Value | Save as variable |
|---|---|---|
| Text | your GitHub PAT | `Token` |
| Text | `ignaciojimenezpi` | `User` |
| Text | `ignaciojimenezpi.github.io` | `Repo` |

### 3. Ask for Album Details

Add three **Ask for Input** actions in sequence:

| Prompt | Input type | Save as variable |
|---|---|---|
| `Album title` | Text | `AlbumTitle` |
| `Date (YYYY-MM-DD)` | Text | `AlbumDate` |
| `Description` | Text | `AlbumDescription` |

### 4. Generate Album ID

1.  Add a **Text** action containing `AlbumTitle`.
2.  Tap the variable → **Lowercase**.
3.  Below that, add **Replace Text**:
    *   Find: ` ` (space)
    *   Replace: `-` (hyphen)
    *   Input: result of previous step
4.  Save result as variable `AlbumID`.

### 5. Read Cover Name from Clipboard

1.  Add **Get Clipboard**.
2.  Save the result as variable `CoverImageName`.

This captures whatever **Copy Cover Name** placed on the clipboard before this shortcut was launched.

### 6. Upload Images (Loop)

Add a **Repeat with Each Item in** action — select **Shortcut Input** as the list.

Inside the loop, add these actions in order:

#### 6a. Get the image filename

1.  Add **Get Details of Images**.
    *   Detail: **Name**
    *   Image: **Repeat Item**
2.  Save the result as variable `ImageStem`.
    *   This gives the filename stem without extension, e.g. `IMG_1234`.

#### 6b. Base64-encode the image

1.  Add **Base64 Encode**.
    *   Input: **Repeat Item**
    *   Line Breaks: **None**
2.  Save the result as variable `EncodedImage`.

#### 6c. Upload the image

Add **Get Contents of URL**:

*   **URL**: `https://api.github.com/repos/` + `User` + `/` + `Repo` + `/contents/photography/staging/` + `AlbumID` + `/` + `ImageStem` + `.jpg`
    > Build this as a **Text** action first, inserting each variable inline, then tap the URL field and select that text variable.
*   **Method**: `PUT`
*   **Headers**:
    *   `Authorization` → `token ` + `Token`
    *   `Accept` → `application/vnd.github.v3+json`
*   **Request Body**: **JSON**
    *   `message` → `Add image ` + `ImageStem`
    *   `content` → `EncodedImage`
    *   `branch` → `main`

**End Repeat** closes the loop.

### 7. Upload Metadata

Build the metadata JSON as a **Text** action (not JSON body — you need to base64-encode it manually):

```
{"title":"AlbumTitle","date":"AlbumDate","description":"AlbumDescription","cover_image":"CoverImageName","favorite":false}
```

Insert each variable inline where shown. Keep it on one line — no line breaks.

Then:

1.  Add **Base64 Encode**.
    *   Input: the Text action above
    *   Line Breaks: **None**
2.  Save result as `EncodedMetadata`.
3.  Add **Get Contents of URL**:
    *   **URL**: `https://api.github.com/repos/` + `User` + `/` + `Repo` + `/contents/photography/staging/` + `AlbumID` + `/metadata.json`
    *   **Method**: `PUT`
    *   **Headers**: same as step 6c
    *   **Request Body**: **JSON**
        *   `message` → `Create album ` + `AlbumID`
        *   `content` → `EncodedMetadata`
        *   `branch` → `main`

> [!IMPORTANT]
> **Order matters**: images must be uploaded before metadata. `metadata.json` is the trigger — the processing workflow fires when it lands, so all images must already be staged.

### 8. Finish

Add **Show Notification**:
*   Title: `Album uploaded`
*   Body: `AlbumID`

---

## Testing

To test without affecting the live site, change `main` to `feature/mobile-album-creation` in every `branch` field across steps 6c and 7, run the shortcut, then verify the **Process Staged Albums** action runs on GitHub. Revert after merging.

## Troubleshooting

**`cover_image` is blank in metadata** — the clipboard was empty when Upload Album ran. Make sure you ran **Copy Cover Name** on the cover photo *before* launching Upload Album.

**`cover_image` shows the wrong photo** — you ran Copy Cover Name on the wrong image, or something else overwrote the clipboard between the two shortcuts. Re-run Copy Cover Name and upload again.

**Upload fails with 422** — the file already exists on that branch. Delete it from the staging folder in GitHub and retry.

**Image name has wrong extension** — `Get Details of Images` → Name gives the stem only; `.jpg` is appended explicitly in step 6c. If your images are not JPEGs, change `.jpg` accordingly or use `Get Details of Images` → **File Extension** and append it dynamically.
