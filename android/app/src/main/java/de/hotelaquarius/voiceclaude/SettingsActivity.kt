package de.hotelaquarius.voiceclaude

import android.os.Bundle
import android.text.InputType
import androidx.appcompat.app.AppCompatActivity
import androidx.preference.EditTextPreference
import androidx.preference.PreferenceFragmentCompat

/**
 * Einstellungen: API-Key, Modell, Modus (Neuer Chat / Claude Code / Cowork),
 * Ziel-URLs sowie Optionen für die Spracheingabe.
 */
class SettingsActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        if (savedInstanceState == null) {
            supportFragmentManager.beginTransaction()
                .replace(R.id.settings_container, SettingsFragment())
                .commit()
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }

    class SettingsFragment : PreferenceFragmentCompat() {
        override fun onCreatePreferences(savedInstanceState: Bundle?, rootKey: String?) {
            setPreferencesFromResource(R.xml.preferences, rootKey)

            // API-Key als Passwortfeld darstellen und in der Übersicht maskieren.
            findPreference<EditTextPreference>(Prefs.KEY_API_KEY)?.apply {
                setOnBindEditTextListener { editText ->
                    editText.inputType =
                        InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
                }
                summaryProvider = EditTextPreference.SummaryProvider<EditTextPreference> { pref ->
                    val value = pref.text.orEmpty()
                    if (value.isBlank()) getString(R.string.api_key_unset)
                    else getString(R.string.api_key_set)
                }
            }
        }
    }
}
