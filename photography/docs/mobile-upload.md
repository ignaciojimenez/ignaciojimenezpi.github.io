# Mobile Album Upload

Create and upload albums directly from your iPhone using iOS Shortcuts.

## Prerequisites

1.  **GitHub Account**
2.  **Fine-grained Personal Access Token (Recommended)**
    *   Go to [Developer Settings > Personal access tokens > Fine-grained tokens](https://github.com/settings/tokens?type=beta).
    *   **Generate new token**.
    *   **Repository access**: Select `ignaciojimenezpi.github.io`.
    *   **Permissions**: `Contents` -> **Read and write**.
    *   **Save the token**.

## iOS Shortcut Setup

### 1. Create Shortcut
*   **Name**: "Upload Album"
*   **Share Sheet**: Enable for **Images**.

### 2. Configure Variables
Add a **Text** action at the top with your details:
*   `Token`: Your GitHub PAT.
*   `User`: `ignaciojimenezpi`
*   `Repo`: `ignaciojimenezpi.github.io`

### 3. Get Album Details
Ask for input and set variables:
1.  **Title** (Text) -> `AlbumTitle`
2.  **Date** (YYYY-MM-DD) -> `AlbumDate`
3.  **Description** (Text) -> `AlbumDescription`
4.  **Cover image index** (Number, default `1`) -> `CoverIndex` *(which image in the selection to use as cover; 1 = first)*

### 4. Generate Album ID
1.  **AlbumID**: Convert `AlbumTitle` to **lowercase** and replace spaces with hyphens (`-`).

### 5. Upload Images (Loop)
Loop through each image input:
1.  **Base64 Encode** image (**Line Breaks: None**).
2.  If `Repeat Index == CoverIndex`, set variable `CoverImageName` to `ImageName`.
3.  **PUT Request**:
    *   **URL**: `https://api.github.com/repos/{User}/{Repo}/contents/photography/staging/{AlbumID}/{ImageName}`
    *   **Headers**: `Authorization: token {Token}`, `Accept: application/vnd.github.v3+json`
    *   **Body**:
        ```json
        {
          "message": "Add image {ImageName}",
          "content": "{Base64Image}",
          "branch": "main"
        }
        ```

### 6. Upload Metadata
1.  **Base64 Encode** the Metadata JSON (**Line Breaks: None**).
2.  **PUT Request**:
    *   **URL**: `https://api.github.com/repos/{User}/{Repo}/contents/photography/staging/{AlbumID}/metadata.json`
    *   **Headers**: Same as above.
    *   **Body**:
        ```json
        {
          "message": "Create album {AlbumID}",
          "content": "{Base64Metadata}",
          "branch": "main"
        }
        ```

**Metadata JSON** (use `CoverImageName` captured in the loop):
```json
{
  "title": "AlbumTitle",
  "date": "AlbumDate",
  "description": "AlbumDescription",
  "cover_image": "CoverImageName",
  "favorite": false
}
```

> [!NOTE]
> **Cover image options**: `cover_image` (filename stem, e.g. `IMG_1234`) is the most reliable approach — capture it during the upload loop as shown in step 5.2. Alternatively, `cover_index` (1-based number) is supported as a fallback, but the index maps to **alphabetical filename order**, which may not match the order images were selected in iOS.

> [!IMPORTANT]
> **Order Matters**: Upload images *before* metadata. `metadata.json` must be the **last** push — it is the only file that triggers the processing workflow, so all images must already be staged when it arrives.

### 7. Finish
Check the response of the last PUT request. If successful, show a notification.

## Testing
To test without affecting the live site:
1.  Change `"branch": "main"` to `"branch": "feature/mobile-album-creation"` in the API requests.
2.  Run the shortcut.
3.  Verify the **"Process Staged Albums"** Action runs on GitHub.
4.  **Revert to "main"** after merging the feature branch.
