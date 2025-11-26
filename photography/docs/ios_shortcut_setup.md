# iOS Shortcut Setup: Remove Album

This guide explains how to create an iOS Shortcut to trigger the album removal workflow on GitHub.

## Prerequisites
- A GitHub Personal Access Token (PAT) with `repo` scope.
- The "Actions" app or just the native "Shortcuts" app on iOS.

## Steps

1.  **Open Shortcuts App**: Create a new shortcut.
2.  **Add "Get Contents of URL" Action**:
    -   **URL**: `https://api.github.com/repos/<your-username>/<your-repo>/dispatches`
        -   Replace `<your-username>` with `ignaciojimenezpi` (or your username).
        -   Replace `<your-repo>` with `ignaciojimenezpi.github.io`.
    -   **Method**: `POST`
    -   **Headers**:
        -   `Accept`: `application/vnd.github.v3+json`
        -   `Authorization`: `Bearer <YOUR_GITHUB_PAT>`
        -   `User-Agent`: `iOS Shortcut`
    -   **Request Body**: `JSON`
        -   Add a field `event_type` with text value `remove_album`.
        -   Add a field `client_payload` of type `Dictionary`.
            -   Inside `client_payload`, add a field `album_id` and set it to "Ask Each Time" (or a specific variable).

## Usage
1.  Run the shortcut.
2.  Enter the `album_id` of the album you want to remove when prompted.
3.  The shortcut will send a request to GitHub, triggering the `remove_album.yml` workflow.

## Verification
-   Check the "Actions" tab in your GitHub repository to see the workflow running.
-   Verify the album is removed from the site.
