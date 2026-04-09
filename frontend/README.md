# Interview Training Mobile Frontend

This Expo React Native app uploads an interview answer recording to the FastAPI backend and renders the coaching response returned by `POST /api/analyze`.

## What it does

- automatically targets the backend running on the same machine during local development
- picks an audio file from the phone
- uploads the file as multipart form data
- shows the returned score, filler words, critique, and improved script

## Setup

1. Start the backend from `/Users/deyandudunovski/Documents/InterviewTrainingApp/backend`.
2. Install dependencies with `npm install`.
3. Start the mobile app with `npm run start`.

## Backend connection

By default the app infers the backend host from the Expo bundle host and calls port `8000`.

If your backend is running somewhere else, you can still override it with `EXPO_PUBLIC_API_BASE_URL` in a frontend `.env` file.
