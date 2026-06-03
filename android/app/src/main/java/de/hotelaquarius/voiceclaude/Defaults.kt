package de.hotelaquarius.voiceclaude

/**
 * Zentrale Standardwerte und Konstanten der App.
 *
 * Die Modus-Werte ([MODE_CHAT], [MODE_CLAUDE_CODE], [MODE_COWORK]) müssen mit den
 * `mode_values` in `res/values/arrays.xml` übereinstimmen.
 */
object Defaults {
    const val DEFAULT_MODEL = "claude-opus-4-8"
    const val DEFAULT_MODE = MODE_CHAT
    const val DEFAULT_LANGUAGE = "de-DE"
    const val DEFAULT_CLAUDE_CODE_URL = "https://claude.ai/code"
    const val DEFAULT_COWORK_URL = "https://claude.ai"
    const val DEFAULT_MAX_TOKENS = 2048

    const val MODE_CHAT = "chat"
    const val MODE_CLAUDE_CODE = "claude_code"
    const val MODE_COWORK = "cowork"
}
