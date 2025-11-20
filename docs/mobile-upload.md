# Mobile Album Upload Setup

This guide explains how to set up an iOS Shortcut to upload photos to your photography portfolio directly from your iPhone.

## Prerequisites

1.  **GitHub Account**: You need a GitHub account.
2.  **Personal Access Token (PAT)**:
    -   Go to [GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)](https://github.com/settings/tokens).
    -   Generate a new token (classic).
    -   Scopes: `repo` (Full control of private repositories).
    -   **Save this token!** You won't see it again.

## iOS Shortcut Setup

You will create a shortcut that takes images as input, asks for details, and uploads them to GitHub.

### Step 1: Create a New Shortcut
1.  Open the **Shortcuts** app on your iPhone.
2.  Tap **+** to create a new shortcut.
3.  Name it "Upload Album".
4.  Enable "Show in Share Sheet" and set it to accept **Images**.

### Step 2: Configure Variables
Add a **Text** action at the top to store your configuration:
-   **Text**: `YOUR_GITHUB_TOKEN` (Paste your PAT here)
-   **Set Variable**: Name it `Token`.
-   **Text**: `ignaciojimenezpi` (Your GitHub username)
-   **Set Variable**: Name it `User`.
-   **Text**: `ignaciojimenezpi.github.io` (Your Repository name)
-   **Set Variable**: Name it `Repo`.

### Step 3: Get Album Details
1.  **Ask for Input**: "Enter Album Title" (Text). Set variable `AlbumTitle`.
2.  **Ask for Input**: "Enter Album Date (YYYY-MM-DD)" (Date, format ISO 8601 if possible, or just Text). Set variable `AlbumDate`.
    -   *Tip: You can use "Current Date" formatted as ISO 8601 if you want today's date.*
3.  **Ask for Input**: "Enter Description (Optional)" (Text). Set variable `AlbumDescription`.

### Step 4: Generate ID and Metadata
1.  **Generate Album ID (Slug)**:
    -   **Change Case**: Pass `AlbumTitle` to this action and set it to **lowercase**.
    -   **Replace Text**: Find ` ` (space) and replace with `-` (hyphen) in the **Updated Text** (result from previous step).
    -   **Set Variable**: Name the result `AlbumID`.
2.  **Dictionary**: Create the metadata JSON structure.
    -   `title`: `AlbumTitle`
    -   `date`: `AlbumDate`
    -   `description`: `AlbumDescription`
    -   `favorite`: `False` (Boolean)
3.  **Get Dictionary from Input**: (This converts it to JSON text).

### Step 5: Upload Metadata
1.  **URL**: `https://api.github.com/repos/ignaciojimenezpi/ignaciojimenezpi.github.io/contents/photography/staging/AlbumID/metadata.json`
    -   Replace `AlbumID` with your variable.
2.  **Base64 Encode**:
    -   Add the **Base64 Encode** action.
    -   Input: The **Dictionary** from Step 4.
    -   **Important**: Tap "Show More" and set **Line Breaks** to **None** (or "Every 76 Characters" is default, but None is safer for JSON payloads, though GitHub usually handles standard Base64). Let's stick to **None** to be safe.
3.  **Get Contents of URL**:
    -   Method: `PUT`
    -   Headers:
        -   `Authorization`: `token Token` (Use variable)
        -   `Accept`: `application/vnd.github.v3+json`
    -   Request Body: JSON
        -   `message`: `Create album AlbumID`
        -   `content`: Select the **Base64 Encoded** result from the previous step.
        -   `branch`: `master` (or `main`)

### Step 6: Upload Images (Loop)
1.  **Repeat with Each** item in `Shortcut Input` (The images).
2.  **Get Name** of `Repeat Item`.
3.  **Base64 Encode** `Repeat Item`.
4.  **URL**: `https://api.github.com/repos/ignaciojimenezpi/ignaciojimenezpi.github.io/contents/photography/staging/AlbumID/RepeatItemName`
    -   Replace `AlbumID` and `RepeatItemName` with variables.
5.  **Get Contents of URL**:
    -   Method: `PUT`
    -   Headers:
        -   `Authorization`: `token Token`
        -   `Accept`: `application/vnd.github.v3+json`
    -   Request Body: JSON
        -   `message`: `Add image RepeatItemName`
        -   `content`: `Base64 Encoded Result`
        -   `branch`: `master` (or `main`)
6.  **End Repeat**.

### Step 7: Finish
1.  **Show Alert**: "Upload Complete! Check GitHub Actions for progress."

## How it Works
1.  The shortcut uploads files to `photography/staging/<album-id>/`.
2.  GitHub detects the push to `photography/staging/`.
3.  A GitHub Action runs `process_staging.py`.
4.  The script processes images, updates `albums.json`, and moves files to `photography/albums/`.
5.  The Action commits the changes.
6.  Cloudflare Pages rebuilds the site.

## Testing on Feature Branch

To test this without affecting your main site:
1.  In your Shortcut, find the API call actions (Step 5 and Step 6).
2.  Change the `branch` field in the JSON body from `master` (or `main`) to `feature/mobile-album-creation`.
3.  Run the shortcut.
4.  Check the "Actions" tab in your GitHub repository to see the "Process Staged Albums" workflow run.
5.  Once successful, you can merge the branch to `master` and update your Shortcut back to `master`.
