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

### 4. Generate ID & Metadata
1.  **AlbumID**: Convert `AlbumTitle` to **lowercase** and replace spaces with hyphens (`-`).
2.  **Metadata JSON**:
    ```json
    {
      "title": "AlbumTitle",
      "date": "AlbumDate",
      "description": "AlbumDescription",
      "favorite": false
    }
    ```

### 5. Upload Images (Loop)
Loop through each image input:
1.  **Base64 Encode** image (**Line Breaks: None**).
2.  **PUT Request**:
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

> [!IMPORTANT]
> **Order Matters**: Upload images *before* metadata. The presence of `metadata.json` triggers the processing workflow.

### 7. Finish
Check the response of the last PUT request. If successful, show a notification.

## Testing
To test without affecting the live site:
1.  Change `"branch": "main"` to `"branch": "feature/mobile-album-creation"` in the API requests.
2.  Run the shortcut.
3.  Verify the **"Process Staged Albums"** Action runs on GitHub.
4.  **Revert to "main"** after merging the feature branch.
