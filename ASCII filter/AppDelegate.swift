import AppKit
import ScreenCaptureKit

class AppDelegate: NSObject, NSApplicationDelegate, ControllerDelegate, NSWindowDelegate {
    private var statusItem: NSStatusItem?
    private var overlayWindow: OverlayWindow?
    private var controllerWindow: ControllerWindow?
    private var watchdog: Watchdog?
    private var captureManager: ScreenCaptureManager?
    
    // Load settings from UserDefaults or use defaults
    var settings = AppSettings.load()
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Start watchdog to monitor main thread responsiveness
        self.watchdog = Watchdog()
        Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
            self?.watchdog?.ping()
        }
        
        // Local emergency quit handler (Option + Shift + Escape)
        NSEvent.addLocalMonitorForEvents(matching: .keyDown) { event in
            if event.modifierFlags.contains([.option, .shift]) && event.keyCode == 53 {
                print("Emergency quit keyboard shortcut triggered!")
                NSApp.terminate(nil)
                return nil
            }
            return event
        }

        // Run as an accessory app so it doesn't show in the Dock or steal focus,
        // but can still show HUD windows.
        NSApp.setActivationPolicy(.accessory)
        
        // Setup status bar item
        setupStatusItem()
        
        // Initialize Metal Device
        guard let device = MTLCreateSystemDefaultDevice() else {
            let alert = NSAlert()
            alert.messageText = "Metal Not Supported"
            alert.informativeText = "ASCII-Lens requires a GPU with Metal support."
            alert.alertStyle = .critical
            alert.runModal()
            NSApp.terminate(nil)
            return
        }
        
        // Create Screen Capture Manager
        captureManager = ScreenCaptureManager(device: device)
        captureManager?.onFrameCaptured = { [weak self] texture in
            self?.overlayWindow?.renderer.updateLatestTexture(texture)
        }
        
        // Create Controller HUD Window
        let controller = ControllerWindow(delegate: self, settings: self.settings)
        self.controllerWindow = controller
        controller.delegate = self
        controller.center()
        controller.makeKeyAndOrderFront(nil)
        
        // Trigger activation of our app so the settings window shows immediately
        NSApp.activate(ignoringOtherApps: true)
        
        // Create Overlay Window (which hosts MTKView & Renderer)
        let screenFrame = NSScreen.main?.frame ?? NSRect(x: 0, y: 0, width: 1920, height: 1080)
        let overlay = OverlayWindow(frame: screenFrame, device: device)
        self.overlayWindow = overlay
        
        // Initial settings application
        applySettings()
        
        // Start screen capture
        if settings.isOverlayEnabled && !(controllerWindow?.isVisible ?? false) {
            showOverlayAndStartCapture()
        }
    }
    
    func applicationWillTerminate(_ notification: Notification) {
        watchdog?.stop()
        captureManager?.stopCapture()
    }
    
    // MARK: - Status Item Setup
    
    private func setupStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let button = statusItem?.button {
            button.title = "📟" // ASCII Terminal Glyph
            button.toolTip = "ASCII-Lens Control"
        }
        
        let menu = NSMenu()
        
        let settingsItem = NSMenuItem(title: "Configuration Panel...", action: #selector(showSettings), keyEquivalent: ",")
        settingsItem.target = self
        menu.addItem(settingsItem)
        
        menu.addItem(NSMenuItem.separator())
        
        let toggleItem = NSMenuItem(title: "Toggle ASCII Overlay", action: #selector(toggleOverlayMenuAction), keyEquivalent: "t")
        toggleItem.target = self
        menu.addItem(toggleItem)
        
        menu.addItem(NSMenuItem.separator())
        
        let quitItem = NSMenuItem(title: "Quit ASCII-Lens", action: #selector(quitApp), keyEquivalent: "q")
        let redQuitTitle = NSAttributedString(string: "Quit ASCII-Lens", attributes: [
            .foregroundColor: NSColor.systemRed
        ])
        quitItem.attributedTitle = redQuitTitle
        quitItem.target = self
        menu.addItem(quitItem)
        
        statusItem?.menu = menu
    }
    
    // MARK: - Actions
    
    @objc func showSettings() {
        if let controller = controllerWindow {
            // Stop the filter while configuring
            hideOverlayAndStopCapture()
            
            controller.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
        }
    }
    
    @objc func toggleOverlayMenuAction() {
        controllerDidToggleOverlay()
    }
    
    @objc func quitApp() {
        controllerDidRequestQuit()
    }
    
    // MARK: - ControllerDelegate
    
    func controllerDidUpdateSettings(_ newSettings: AppSettings) {
        let fpsChanged = (settings.targetFps != newSettings.targetFps)
        let overlayStateChanged = (settings.isOverlayEnabled != newSettings.isOverlayEnabled)
        
        self.settings = newSettings
        settings.save()
        
        applySettings()
        
        if fpsChanged {
            captureManager?.updateFps(newSettings.targetFps)
        }
        
        if overlayStateChanged {
            if newSettings.isOverlayEnabled {
                if let controller = controllerWindow, !controller.isVisible {
                    showOverlayAndStartCapture()
                } else {
                    controllerWindow?.close()
                }
            } else {
                hideOverlayAndStopCapture()
            }
        }
    }
    
    func controllerDidToggleOverlay() {
        var updatedSettings = settings
        updatedSettings.isOverlayEnabled.toggle()
        controllerWindow?.updateOverlayButtonState(isEnabled: updatedSettings.isOverlayEnabled)
        controllerDidUpdateSettings(updatedSettings)
    }
    
    func controllerDidRequestQuit() {
        hideOverlayAndStopCapture()
        NSApp.terminate(nil)
    }
    
    // MARK: - NSWindowDelegate
    
    func windowWillClose(_ notification: Notification) {
        if notification.object as? ControllerWindow != nil {
            // Resume ASCII filter if it was enabled
            if settings.isOverlayEnabled {
                showOverlayAndStartCapture()
            }
        }
    }
    
    // MARK: - Helper Methods
    
    private func applySettings() {
        overlayWindow?.renderer.updateSettings(settings)
    }
    
    private func showOverlayAndStartCapture() {
        guard let overlay = overlayWindow else { return }
        
        // Show window on screen
        overlay.orderFrontRegardless()
        
        // Exclude our own windows from the capture to prevent feedback loops.
        // Wait, ScreenCaptureKit shareable content needs to know which windows to exclude.
        // We will fetch windows on the main thread and update our capture filter.
        SCShareableContent.getWithCompletionHandler { [weak self] content, error in
            guard let self = self, let content = content, error == nil else { return }
            
            let myPid = ProcessInfo.processInfo.processIdentifier
            let excludeWindows = content.windows.filter { $0.owningApplication?.processID == myPid }
            
            DispatchQueue.main.async {
                self.captureManager?.startCapture(excluding: excludeWindows, targetFps: self.settings.targetFps)
            }
        }
    }
    
    private func hideOverlayAndStopCapture() {
        overlayWindow?.orderOut(nil)
        captureManager?.stopCapture()
    }
}

// MARK: - Watchdog Failsafe
class Watchdog {
    private var lastPingTime = Date()
    private var isRunning = true
    private let lock = NSLock()
    
    init() {
        Thread.detachNewThread { [weak self] in
            self?.runLoop()
        }
    }
    
    func ping() {
        lock.lock()
        lastPingTime = Date()
        lock.unlock()
    }
    
    func stop() {
        lock.lock()
        isRunning = false
        lock.unlock()
    }
    
    private func runLoop() {
        while true {
            Thread.sleep(forTimeInterval: 1.0)
            
            lock.lock()
            let active = isRunning
            let lastPing = lastPingTime
            lock.unlock()
            
            if !active { break }
            
            let elapsed = Date().timeIntervalSince(lastPing)
            if elapsed > 3.0 {
                print("=== WATCHDOG DETECTED FREEZE ===")
                print("Main thread unresponsive for \(elapsed) seconds. Self-terminating app to protect the OS.")
                print("=================================")
                exit(1)
            }
        }
    }
}
