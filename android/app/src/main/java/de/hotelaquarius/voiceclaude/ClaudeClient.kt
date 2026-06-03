package de.hotelaquarius.voiceclaude

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/** Fehler bei der Kommunikation mit der Anthropic-API. */
class ClaudeException(message: String) : Exception(message)

/**
 * Kapselt die Kommunikation mit der Anthropic Messages API.
 *
 * @param apiKey Der persönliche Anthropic-API-Key (Header `x-api-key`).
 */
class ClaudeClient(private val apiKey: String) {

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)
        .build()

    /**
     * Schickt [prompt] an das gewählte [model] und gibt die zusammengesetzte Textantwort zurück.
     *
     * @throws ClaudeException bei API- oder Netzwerkfehlern.
     */
    suspend fun sendMessage(
        prompt: String,
        model: String,
        maxTokens: Int = Defaults.DEFAULT_MAX_TOKENS
    ): String = withContext(Dispatchers.IO) {
        val message = JSONObject()
            .put("role", "user")
            .put("content", prompt)

        val payload = JSONObject()
            .put("model", model)
            .put("max_tokens", maxTokens)
            .put("messages", JSONArray().put(message))
            .toString()
            .toRequestBody("application/json".toMediaType())

        val request = Request.Builder()
            .url("https://api.anthropic.com/v1/messages")
            .header("x-api-key", apiKey)
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .post(payload)
            .build()

        try {
            client.newCall(request).execute().use { response ->
                val raw = response.body?.string().orEmpty()
                if (!response.isSuccessful) {
                    val msg = runCatching {
                        JSONObject(raw).getJSONObject("error").getString("message")
                    }.getOrDefault("HTTP ${response.code}")
                    throw ClaudeException(msg)
                }
                parseText(raw)
            }
        } catch (e: ClaudeException) {
            throw e
        } catch (e: Exception) {
            throw ClaudeException(e.message ?: "Netzwerkfehler")
        }
    }

    /** Setzt alle Text-Blöcke der Antwort zu einem String zusammen. */
    private fun parseText(raw: String): String {
        val content = JSONObject(raw).optJSONArray("content") ?: return ""
        val sb = StringBuilder()
        for (i in 0 until content.length()) {
            val block = content.optJSONObject(i) ?: continue
            if (block.optString("type") == "text") {
                sb.append(block.optString("text"))
            }
        }
        return sb.toString().ifBlank { "(Keine Textantwort erhalten)" }
    }
}
