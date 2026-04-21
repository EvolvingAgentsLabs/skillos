import Foundation
import Capacitor

/**
 * LiteRT-LM iOS plugin — STUB.
 *
 * Google's LiteRT-LM Swift SDK is marked "in dev" as of 2026-04. Until the
 * stable Swift API ships, this stub reports unavailable and throws on
 * every call. The TS `pickBackendForModel` factory detects this via
 * `isAvailable()` and routes iOS traffic to the wllama WASM backend
 * instead.
 */
@objc(LiteRTLMPlugin)
public class LiteRTLMPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "LiteRTLMPlugin"
    public let jsName = "LiteRTLM"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "isAvailable", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "initModel", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "generate", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "cancel", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "unloadModel", returnType: CAPPluginReturnPromise)
    ]

    @objc func isAvailable(_ call: CAPPluginCall) {
        call.resolve(["available": false])
    }

    @objc func initModel(_ call: CAPPluginCall) {
        call.reject("LiteRT-LM iOS SDK is not yet available. Use wllama backend instead.")
    }

    @objc func generate(_ call: CAPPluginCall) {
        call.reject("LiteRT-LM iOS SDK is not yet available.")
    }

    @objc func cancel(_ call: CAPPluginCall) {
        call.resolve()
    }

    @objc func unloadModel(_ call: CAPPluginCall) {
        call.resolve()
    }
}
