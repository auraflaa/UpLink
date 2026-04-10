# UpLink – Cognitive Execution System (Frontend)

This is the front-end application for **UpLink**, an AI-driven personal intelligence system tailored for students. UpLink aims to transform fragmented digital activity (GitHub commits, hackathons, notes) into actionable insights and an automated execution layer.

> **Note:** This repository directory contains only the Frontend User Interface.

## 🚀 Tech Stack

*   **Framework**: React 18
*   **Language**: TypeScript
*   **Bundler**: Vite (for ultra-fast Hot Module Replacement)
*   **Routing**: React Router DOM (v6)
*   **Styling**: Pure Vanilla CSS (`index.css`)
    *   *Design System highlights:* Custom abstract `bg-blobs`, highly-polished glassmorphism (`glass-panel`), modern typography (`Outfit` & `Inter`).
*   **Icons**: Lucide React

## 🗺️ Application Architecture / Routes

The client-side routing is configured to mirror the core UpLink flow:

1.  **`/` (Landing Page)**: Hero section showcasing the closed-loop execution loop and problem statements.
2.  **`/login` (Login Page)**: A completely immersive, distraction-free authentication experience.
3.  **`/home` (Dashboard)**: The central nervous system showing data sources, quick routing, and an active "Execution Layer Activity" feed.
4.  **`/github-analyzer` (GitHub Repo Analyzer)**: Link ingestion and prompt inputs directly querying project architecture for Semantic Intelligence Insights.
5.  **`/resume-upload` (Document Ingestion)**: Interactive drag-and-drop ingestion interface simulating data extraction for the Vector DB.

## 🛠️ Getting Started Locally

### Prerequisites
* Ensure you have [Node.js](https://nodejs.org/) installed (v18+ recommended).

### Installation
From inside this `Frontend` directory, install the required packages:
```bash
npm install
```

### Running the Application (Development)
You can instantly start the UI by running the provided batch script:
1. Double-click the `run_frontend.bat` file in your file explorer.
   
**OR** via the terminal:
```bash
npm run dev
```

This will deploy the application at `http://localhost:5173/`.

### Production Build
To create an optimized production build:
```bash
npm run build
```
This will compile the TypeScript, bundle the React application, and output the production-ready assets to the `/dist` directory.
