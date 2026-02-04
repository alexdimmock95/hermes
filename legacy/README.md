# Legacy Features

This folder contains archived features that are no longer actively used in the main project, but may be valuable for future development.

## Contents

### `app/` — Gradio Web Interface
A Gradio-based web UI for audio processing. This was used before the Telegram bot became the primary interface.

**Why archived:** The Telegram bot (`src/telegram_bot.py`) is now the main user interface for voice translation and dictionary lookups.

**Future potential:** Could be useful if you want to add a web-based dashboard or alternative UI interface.

### `demo/` — Standalone Demo Script
A procedural demonstration script that orchestrates the full accent softening pipeline end-to-end.

**Why archived:** Now integrated into the Telegram bot workflow.

**Future potential:** Useful for testing, debugging, or understanding the pipeline flow in isolation.

## Note on Voice Transformation

The `voice_transformer.py` module (using WORLD vocoder) is **NOT** in legacy — it's still in `src/` and can be integrated into the Telegram bot for gender/age voice modification features.

## Restoring Features

If you need to bring back the Gradio app or demo:
```bash
# Move back to root level
mv legacy/app .
mv legacy/demo .
```
