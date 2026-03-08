# Quotes Module - Quote Card Image Generation

## Overview
Generates poster-style quote card images. Used by the !quote command. Creates a PNG with the quoted message, username, and timestamp over a blurred avatar background.

## Input
- avatar_bytes: Raw image bytes of the user's profile picture
- username: Display name
- content: The message text to quote (truncated to 500 chars by the caller)
- timestamp: When the message was sent

## Process

### Layout
- Fixed width (1200px), height grows with text length
- Avatar is scaled to cover the full image, with slight Gaussian blur
- A black gradient overlay at the bottom creates a readable area for text
- Text is centered with heavy drop shadows for legibility

### Text
- Username: Large font (64pt), white
- Quoted content: Wrapped to fit width, medium font (52pt)
- Timestamp: Smaller font (32pt), muted color, formatted like "Mar 7, 2025 at 2:55 PM"

### Fonts
Tries Papyrus first (macOS/Windows paths), then falls back to Arial, DejaVu Sans, or system default. Uses Pillow (PIL) for image manipulation.

### Output
Returns PNG bytes. The bot sends this as a Discord file attachment.
