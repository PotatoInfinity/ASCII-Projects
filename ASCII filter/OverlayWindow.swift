import AppKit
import MetalKit

class OverlayWindow: NSWindow {
    let renderer: ASCIIFilterRenderer
    let mtkView: MTKView
    
    init(frame: NSRect, device: MTLDevice) {
        // Initialize renderer
        self.renderer = ASCIIFilterRenderer(device: device)
        
        // Create MTKView matching window frame
        self.mtkView = MTKView(frame: NSRect(origin: .zero, size: frame.size), device: device)
        
        super.init(
            contentRect: frame,
            styleMask: [.borderless, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        
        // Window behaviors for system-wide ghost overlay
        self.isReleasedWhenClosed = false
        self.level = .screenSaver // Keeps the window above dock, menu bar, and windows
        self.backgroundColor = .clear
        self.isOpaque = false
        self.hasShadow = false
        self.ignoresMouseEvents = true // Direct clicks to windows beneath us
        
        // Make window display on all virtual desktops/Spaces and remain stationary
        self.collectionBehavior = [.canJoinAllSpaces, .stationary, .ignoresCycle]
        
        // Configure MTKView properties
        mtkView.delegate = renderer
        mtkView.clearColor = MTLClearColor(red: 0, green: 0, blue: 0, alpha: 0) // Transparent clear color
        mtkView.framebufferOnly = false // Required for compute shader write operations
        mtkView.isPaused = true // Render only on-demand when frames arrive
        mtkView.enableSetNeedsDisplay = false
        
        // Connect renderer back to view
        renderer.view = mtkView
        
        // Set view hierarchy
        self.contentView = mtkView
    }
    
    override var canBecomeKey: Bool {
        return false // Never steal keyboard/focus from active apps
    }
    
    override var canBecomeMain: Bool {
        return false
    }
}
