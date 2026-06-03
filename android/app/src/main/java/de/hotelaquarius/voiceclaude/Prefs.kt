package de.hotelaquarius.voiceclaude

import android.content.Context
import androidx.preference.PreferenceManager

/**
 * Liest die in den Einstellungen gespeicherten Werte aus.
 *
 * Die Werte liegen in den app-privaten Standard-SharedPreferences und sind damit
 * nur für diese App zugänglich (Android-Sandbox).
 */
class Prefs(context: Context) {

    private val sp = PreferenceManager.getDefaultSharedPreferences(context)

    val apiKey: String
        get() = sp.getString(KEY_API_KEY, "").orEmpty().trim()

    val model: String
        get() = sp.getString(KEY_MODEL, Defaults.DEFAULT_MODEL) ?: Defaults.DEFAULT_MODEL

    val mode: String
        get() = sp.getString(KEY_MODE, Defaults.DEFAULT_MODE) ?: Defaults.DEFAULT_MODE

    val language: String
        get() = sp.getString(KEY_LANGUAGE, Defaults.DEFAULT_LANGUAGE) ?: Defaults.DEFAULT_LANGUAGE

    val autoStartMic: Boolean
        get() = sp.getBoolean(KEY_AUTOSTART, true)

    val autoSend: Boolean
        get() = sp.getBoolean(KEY_AUTOSEND, true)

    val claudeCodeUrl: String
        get() = sp.getString(KEY_CC_URL, Defaults.DEFAULT_CLAUDE_CODE_URL)
            ?.ifBlank { Defaults.DEFAULT_CLAUDE_CODE_URL } ?: Defaults.DEFAULT_CLAUDE_CODE_URL

    val coworkUrl: String
        get() = sp.getString(KEY_COWORK_URL, Defaults.DEFAULT_COWORK_URL)
            ?.ifBlank { Defaults.DEFAULT_COWORK_URL } ?: Defaults.DEFAULT_COWORK_URL

    companion object {
        const val KEY_API_KEY = "api_key"
        const val KEY_MODEL = "model"
        const val KEY_MODE = "mode"
        const val KEY_LANGUAGE = "language"
        const val KEY_AUTOSTART = "autostart_mic"
        const val KEY_AUTOSEND = "auto_send"
        const val KEY_CC_URL = "claude_code_url"
        const val KEY_COWORK_URL = "cowork_url"
    }
}
