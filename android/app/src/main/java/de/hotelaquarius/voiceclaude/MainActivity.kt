package de.hotelaquarius.voiceclaude

import android.Manifest
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.view.Menu
import android.view.MenuItem
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import de.hotelaquarius.voiceclaude.databinding.ActivityMainBinding
import kotlinx.coroutines.launch

/**
 * Hauptbildschirm.
 *
 * Ablauf: Beim Start wird (sofern aktiviert) das Mikrofon gestartet, das Gesprochene
 * per Spracherkennung in Text gewandelt und – je nach gewähltem Modus – an die
 * Claude-API geschickt oder an eine Claude-Oberfläche (Claude Code / Cowork) übergeben.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var prefs: Prefs
    private var recognizer: SpeechRecognizer? = null

    private val micPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) startListening()
            else setStatus(getString(R.string.status_no_mic_permission))
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        prefs = Prefs(this)

        setSupportActionBar(binding.toolbar)

        binding.micButton.setOnClickListener { ensureMicAndListen() }
        binding.sendButton.setOnClickListener { dispatch(binding.transcript.text.toString()) }
    }

    override fun onStart() {
        super.onStart()
        // Anforderung: Beim Start automatisch das Mikrofon aktivieren.
        // Kann in den Einstellungen abgeschaltet werden.
        if (prefs.autoStartMic) ensureMicAndListen()
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.main_menu, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return if (item.itemId == R.id.action_settings) {
            startActivity(Intent(this, SettingsActivity::class.java))
            true
        } else {
            super.onOptionsItemSelected(item)
        }
    }

    /** Prüft die Mikrofon-Berechtigung und startet danach die Spracherkennung. */
    private fun ensureMicAndListen() {
        val granted = ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) ==
            PackageManager.PERMISSION_GRANTED
        if (granted) startListening() else micPermission.launch(Manifest.permission.RECORD_AUDIO)
    }

    private fun startListening() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            setStatus(getString(R.string.status_no_recognizer))
            return
        }
        recognizer?.destroy()
        recognizer = SpeechRecognizer.createSpeechRecognizer(this).apply {
            setRecognitionListener(listener)
        }
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, prefs.language)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
        }
        setStatus(getString(R.string.status_listening))
        binding.transcript.setText("")
        recognizer?.startListening(intent)
    }

    private val listener = object : RecognitionListener {
        override fun onReadyForSpeech(params: Bundle?) {}
        override fun onBeginningOfSpeech() {}
        override fun onRmsChanged(rmsdB: Float) {}
        override fun onBufferReceived(buffer: ByteArray?) {}
        override fun onEndOfSpeech() = setStatus(getString(R.string.status_processing))

        override fun onError(error: Int) {
            setStatus(getString(R.string.status_error_speech, error))
        }

        override fun onResults(results: Bundle?) {
            val text = results
                ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                ?.firstOrNull()
                .orEmpty()
            binding.transcript.setText(text)
            if (text.isNotBlank() && prefs.autoSend) dispatch(text)
            else setStatus(getString(R.string.status_idle))
        }

        override fun onPartialResults(partialResults: Bundle?) {
            val text = partialResults
                ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                ?.firstOrNull()
                .orEmpty()
            if (text.isNotBlank()) binding.transcript.setText(text)
        }

        override fun onEvent(eventType: Int, params: Bundle?) {}
    }

    /** Verteilt den erkannten Text je nach gewähltem Modus. */
    private fun dispatch(prompt: String) {
        val text = prompt.trim()
        if (text.isBlank()) {
            setStatus(getString(R.string.status_empty))
            return
        }
        when (prefs.mode) {
            Defaults.MODE_CLAUDE_CODE ->
                handOff(text, prefs.claudeCodeUrl, getString(R.string.mode_claude_code))
            Defaults.MODE_COWORK ->
                handOff(text, prefs.coworkUrl, getString(R.string.mode_cowork))
            else ->
                sendToApi(text)
        }
    }

    /** Modus „Neuer Chat": Prompt direkt an die Anthropic-API senden. */
    private fun sendToApi(prompt: String) {
        val key = prefs.apiKey
        if (key.isBlank()) {
            setStatus(getString(R.string.status_no_api_key))
            startActivity(Intent(this, SettingsActivity::class.java))
            return
        }
        setStatus(getString(R.string.status_sending, prefs.model))
        binding.response.text = ""
        binding.sendButton.isEnabled = false
        lifecycleScope.launch {
            try {
                val answer = ClaudeClient(key).sendMessage(prompt, prefs.model)
                binding.response.text = answer
                setStatus(getString(R.string.status_done))
            } catch (e: Exception) {
                binding.response.text = getString(R.string.error_prefix, e.message ?: "Unbekannt")
                setStatus(getString(R.string.status_error))
            } finally {
                binding.sendButton.isEnabled = true
            }
        }
    }

    /**
     * Modus „Claude Code" / „Cowork": Da es keine öffentliche Schnittstelle zum
     * Vorbefüllen einer Sitzung gibt, wird der Text in die Zwischenablage kopiert und
     * die jeweilige Claude-Oberfläche geöffnet – dort kann er eingefügt werden.
     */
    private fun handOff(prompt: String, url: String, label: String) {
        val cm = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        cm.setPrimaryClip(ClipData.newPlainText("Claude Prompt", prompt))
        Toast.makeText(this, getString(R.string.toast_copied, label), Toast.LENGTH_LONG).show()
        binding.response.text = getString(R.string.handoff_hint, label, prompt)
        runCatching {
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        }.onFailure {
            setStatus(getString(R.string.status_error))
        }
    }

    private fun setStatus(text: String) {
        binding.status.text = text
    }

    override fun onDestroy() {
        recognizer?.destroy()
        recognizer = null
        super.onDestroy()
    }
}
