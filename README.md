# StoryBook

A modern web application for reading and discovering stories with an interactive reader experience.

## Features

- 📖 **Story Reader** — Read stories page by page with a clean, distraction-free interface
- 📱 **Responsive Design** — Optimized for desktop and mobile devices
- ⬅️➡️ **Navigation** — Easy prev/next navigation between pages
- 👆 **Swipe Support** — Navigate stories using touch gestures on mobile
- 🔐 **Google Authentication** — Secure login with your Google account
- 🌐 **Cloud Hosted** — Fast, reliable content delivery via Azure

## Live Website

Visit the application here: **https://calm-flower-03619f100.7.azurestaticapps.net**

## Getting Started

### Prerequisites
- Modern web browser with JavaScript enabled
- Google account for authentication

### How to Use

1. Navigate to the [StoryBook website](https://calm-flower-03619f100.7.azurestaticapps.net)
2. Click **Login with Google** to authenticate
3. Browse available stories from the library
4. Click on a story to start reading
5. Use the next/previous buttons or swipe to navigate between pages

## Technical Stack

- **Frontend:** HTML, CSS, JavaScript
- **Hosting:** Azure Static Web Apps (Standard plan)
- **Authentication:** Google OAuth 2.0
- **Storage:** Azure Blob Storage
- **CI/CD:** GitHub Actions

## Architecture

- `index.html` — Story library and listing page
- `reader.html` — Story reading interface
- `js/stories.js` — Story fetching and rendering logic
- `js/reader.js` — Page navigation and swipe handling
- `js/config.js` — Azure Blob Storage configuration (auto-generated)
- `staticwebapp.config.json` — Authentication and routing configuration

## Development

### Local Setup

1. Clone the repository
2. Create `js/config.js` based on `js/config.example.js`
3. Add your Azure Blob Storage credentials
4. Open `index.html` in a web browser

### Deployment

The project uses GitHub Actions for automated deployment:
- Changes pushed to `master` branch automatically trigger deployment to Azure Static Web Apps
- Secrets (`BLOB_BASE`, `BLOB_SAS`, `AZURE_STATIC_WEB_APPS_API_TOKEN`) are managed in GitHub Settings

## Author

Created by Harry Zhao

## License

All rights reserved.
