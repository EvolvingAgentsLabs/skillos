package com.skillos.litert

import com.getcapacitor.JSObject
import com.getcapacitor.Plugin
import com.getcapacitor.PluginCall
import com.getcapacitor.PluginMethod
import com.getcapacitor.annotation.CapacitorPlugin
import com.google.ai.edge.litertlm.LlmInference
import com.google.ai.edge.litertlm.LlmInferenceOptions
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import java.util.concurrent.ConcurrentHashMap
import java.util.UUID

/**
 * LiteRT-LM Capacitor plugin (Android).
 *
 * Exposes four methods (initModel / generate / cancel / unloadModel) and
 * three events (token / done / error). The TS `LiteRTBackend` in
 * `mobile/src/lib/llm/local/litert_backend.ts` drives this.
 *
 * Note: the Android LiteRT-LM SDK API may evolve; this file assumes the
 * 0.1.0 surface with LlmInference + LlmInferenceOptions. Bump the gradle
 * pin deliberately rather than using a + wildcard.
 */
@CapacitorPlugin(name = "LiteRTLM")
class LiteRTLMPlugin : Plugin() {
    private val sessions = ConcurrentHashMap<String, LlmInference>()
    private val activeJobs = ConcurrentHashMap<String, Job>()
    private val scope = CoroutineScope(Dispatchers.Default)

    @PluginMethod
    fun isAvailable(call: PluginCall) {
        val result = JSObject()
        result.put("available", true)
        call.resolve(result)
    }

    @PluginMethod
    fun initModel(call: PluginCall) {
        val modelPath = call.getString("modelPath") ?: run {
            call.reject("modelPath required")
            return
        }
        scope.launch {
            try {
                val options = LlmInferenceOptions.builder()
                    .setModelPath(modelPath)
                    .build()
                val inference = LlmInference.createFromOptions(context, options)
                val handle = UUID.randomUUID().toString()
                sessions[handle] = inference
                val result = JSObject()
                result.put("handle", handle)
                call.resolve(result)
            } catch (e: Throwable) {
                call.reject("initModel failed: ${e.message}", e)
            }
        }
    }

    @PluginMethod
    fun generate(call: PluginCall) {
        val handle = call.getString("handle") ?: run {
            call.reject("handle required")
            return
        }
        val prompt = call.getString("prompt") ?: run {
            call.reject("prompt required")
            return
        }
        val inference = sessions[handle] ?: run {
            call.reject("unknown handle: $handle")
            return
        }

        val job = scope.launch {
            try {
                val builder = StringBuilder()
                inference.generateResponseAsync(prompt) { partialResult, done ->
                    if (partialResult != null) {
                        builder.append(partialResult)
                        val evt = JSObject()
                        evt.put("handle", handle)
                        evt.put("delta", partialResult)
                        notifyListeners("token", evt)
                    }
                    if (done) {
                        val evt = JSObject()
                        evt.put("handle", handle)
                        evt.put("text", builder.toString())
                        evt.put("finishReason", "stop")
                        notifyListeners("done", evt)
                    }
                }
                call.resolve()
            } catch (e: Throwable) {
                val evt = JSObject()
                evt.put("handle", handle)
                evt.put("message", e.message ?: "error")
                notifyListeners("error", evt)
                call.reject("generate failed: ${e.message}", e)
            } finally {
                activeJobs.remove(handle)
            }
        }
        activeJobs[handle] = job
    }

    @PluginMethod
    fun cancel(call: PluginCall) {
        val handle = call.getString("handle") ?: run {
            call.resolve()
            return
        }
        activeJobs[handle]?.cancel()
        activeJobs.remove(handle)
        call.resolve()
    }

    @PluginMethod
    fun unloadModel(call: PluginCall) {
        val handle = call.getString("handle") ?: run {
            call.resolve()
            return
        }
        activeJobs[handle]?.cancel()
        activeJobs.remove(handle)
        val inference = sessions.remove(handle)
        try {
            inference?.close()
        } catch (_: Throwable) { }
        call.resolve()
    }

    override fun handleOnPause() {
        // Cancel any in-flight inference so we don't leak across lifecycle.
        activeJobs.values.forEach { it.cancel() }
        activeJobs.clear()
        super.handleOnPause()
    }

    override fun handleOnDestroy() {
        scope.cancel()
        sessions.values.forEach {
            try { it.close() } catch (_: Throwable) { }
        }
        sessions.clear()
        super.handleOnDestroy()
    }
}
