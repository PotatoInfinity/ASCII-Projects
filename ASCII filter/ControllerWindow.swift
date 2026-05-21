import AppKit

struct AppSettings: Codable {
    var tileSize: Int = 12
    var opacity: Float = 0.8
    var charSetIndex: Int = 0
    var colorMode: Int = 0 // 0 = Full Color, 1 = Matrix Green, 2 = Amber, 3 = White
    var enableEdgeEnhancement: Bool = true
    var edgeThreshold: Float = 0.15
    var targetFps: Int = 60
    var isOverlayEnabled: Bool = true
    var neuralEnhancement: Bool = false
}

extension AppSettings {
    static func load() -> AppSettings {
        guard let data = UserDefaults.standard.data(forKey: "AppSettings") else {
            return AppSettings()
        }
        do {
            return try JSONDecoder().decode(AppSettings.self, from: data)
        } catch {
            print("Failed to decode AppSettings: \(error)")
            return AppSettings()
        }
    }
    
    func save() {
        do {
            let data = try JSONEncoder().encode(self)
            UserDefaults.standard.set(data, forKey: "AppSettings")
        } catch {
            print("Failed to encode AppSettings: \(error)")
        }
    }
}

protocol ControllerDelegate: AnyObject {
    func controllerDidUpdateSettings(_ settings: AppSettings)
    func controllerDidToggleOverlay()
    func controllerDidRequestQuit()
}

class ControllerWindow: NSPanel {
    private weak var controllerDelegate: ControllerDelegate?
    private var settings: AppSettings
    
    // UI Controls
    private let titleLabel = NSTextField(labelWithString: "ASCII-Lens Controls")
    
    private let tileSizeLabel = NSTextField(labelWithString: "Tile Size: 12px")
    private let tileSizeSlider = NSSlider()
    
    private let opacityLabel = NSTextField(labelWithString: "ASCII Opacity: 80%")
    private let opacitySlider = NSSlider()
    
    private let charSetLabel = NSTextField(labelWithString: "Character Set:")
    private let charSetPopup = NSPopUpButton()
    
    private let colorModeLabel = NSTextField(labelWithString: "Color Style:")
    private let colorModePopup = NSPopUpButton()
    
    private let edgeCheckbox = NSButton()
    private let edgeThresholdLabel = NSTextField(labelWithString: "Edge Sensitivity: 0.15")
    private let edgeThresholdSlider = NSSlider()
    
    private let fpsLabel = NSTextField(labelWithString: "Refresh Rate:")
    private let fpsSegmented = NSSegmentedControl()
    
    private let toggleOverlayButton = NSButton()
    private let quitButton = NSButton()
    private let neuralCheckbox = NSButton()
    
    init(delegate: ControllerDelegate, settings: AppSettings) {
        self.controllerDelegate = delegate
        self.settings = settings
        
        super.init(
            contentRect: NSRect(x: 100, y: 100, width: 300, height: 510),
            styleMask: [.titled, .closable, .hudWindow, .utilityWindow, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        
        self.title = "ASCII-Lens Controller"
        self.isFloatingPanel = true
        self.level = .statusBar // Float above menu bar and status items (always on top)
        self.hidesOnDeactivate = false
        self.isReleasedWhenClosed = false
        
        setupUI()
    }
    
    private func setupUI() {
        let mainStack = NSStackView()
        mainStack.orientation = .vertical
        mainStack.alignment = .centerX
        mainStack.spacing = 16
        mainStack.edgeInsets = NSEdgeInsets(top: 20, left: 20, bottom: 20, right: 20)
        mainStack.translatesAutoresizingMaskIntoConstraints = false
        
        // Font setup (Menlo for retro feel)
        let monoFont = NSFont(name: "Menlo-Bold", size: 14) ?? NSFont.boldSystemFont(ofSize: 14)
        let labelFont = NSFont(name: "Menlo", size: 11) ?? NSFont.systemFont(ofSize: 11)
        
        // Title
        titleLabel.font = monoFont
        titleLabel.textColor = NSColor(red: 0.0, green: 1.0, blue: 0.2, alpha: 1.0) // Matrix Green
        mainStack.addView(titleLabel, in: .top)
        
        // Helper to format labels
        let configureLabel = { (label: NSTextField) in
            label.font = labelFont
            label.alignment = .left
            label.translatesAutoresizingMaskIntoConstraints = false
        }
        
        // --- Tile Size Row ---
        let tileSizeStack = NSStackView()
        tileSizeStack.orientation = .vertical
        tileSizeStack.alignment = .leading
        tileSizeStack.spacing = 4
        tileSizeStack.translatesAutoresizingMaskIntoConstraints = false
        
        configureLabel(tileSizeLabel)
        tileSizeSlider.minValue = 2.0
        tileSizeSlider.maxValue = 32.0
        tileSizeSlider.doubleValue = Double(settings.tileSize)
        tileSizeSlider.target = self
        tileSizeSlider.action = #selector(tileSizeChanged)
        
        tileSizeStack.addView(tileSizeLabel, in: .top)
        tileSizeStack.addView(tileSizeSlider, in: .top)
        mainStack.addView(tileSizeStack, in: .top)
        
        // --- Opacity Row ---
        let opacityStack = NSStackView()
        opacityStack.orientation = .vertical
        opacityStack.alignment = .leading
        opacityStack.spacing = 4
        opacityStack.translatesAutoresizingMaskIntoConstraints = false
        
        configureLabel(opacityLabel)
        opacitySlider.minValue = 0.0
        opacitySlider.maxValue = 1.0
        opacitySlider.doubleValue = Double(settings.opacity)
        opacitySlider.target = self
        opacitySlider.action = #selector(opacityChanged)
        
        opacityStack.addView(opacityLabel, in: .top)
        opacityStack.addView(opacitySlider, in: .top)
        mainStack.addView(opacityStack, in: .top)
        
        // --- Character Set Row ---
        let charSetStack = NSStackView()
        charSetStack.orientation = .vertical
        charSetStack.alignment = .leading
        charSetStack.spacing = 4
        charSetStack.translatesAutoresizingMaskIntoConstraints = false
        
        configureLabel(charSetLabel)
        charSetPopup.addItems(withTitles: ["Standard ASCII", "Blocky Blocks", "Extended ASCII", "Matrix Code"])
        charSetPopup.selectItem(at: settings.charSetIndex)
        charSetPopup.target = self
        charSetPopup.action = #selector(charSetChanged)
        charSetPopup.translatesAutoresizingMaskIntoConstraints = false
        
        charSetStack.addView(charSetLabel, in: .top)
        charSetStack.addView(charSetPopup, in: .top)
        mainStack.addView(charSetStack, in: .top)
        
        // --- Color Mode Row ---
        let colorModeStack = NSStackView()
        colorModeStack.orientation = .vertical
        colorModeStack.alignment = .leading
        colorModeStack.spacing = 4
        colorModeStack.translatesAutoresizingMaskIntoConstraints = false
        
        configureLabel(colorModeLabel)
        colorModePopup.addItems(withTitles: ["Full Color", "Matrix Green", "Phosphor Amber", "Mono White"])
        colorModePopup.selectItem(at: settings.colorMode)
        colorModePopup.target = self
        colorModePopup.action = #selector(colorModeChanged)
        colorModePopup.translatesAutoresizingMaskIntoConstraints = false
        
        colorModeStack.addView(colorModeLabel, in: .top)
        colorModeStack.addView(colorModePopup, in: .top)
        mainStack.addView(colorModeStack, in: .top)
        
        // --- Edge Detection Row ---
        let edgeStack = NSStackView()
        edgeStack.orientation = .vertical
        edgeStack.alignment = .leading
        edgeStack.spacing = 4
        edgeStack.translatesAutoresizingMaskIntoConstraints = false
        
        edgeCheckbox.setButtonType(.switch)
        edgeCheckbox.title = "Enhance Outlines"
        edgeCheckbox.state = settings.enableEdgeEnhancement ? .on : .off
        edgeCheckbox.font = labelFont
        edgeCheckbox.target = self
        edgeCheckbox.action = #selector(edgeCheckboxChanged)
        
        configureLabel(edgeThresholdLabel)
        edgeThresholdSlider.minValue = 0.05
        edgeThresholdSlider.maxValue = 0.4
        edgeThresholdSlider.doubleValue = Double(settings.edgeThreshold)
        edgeThresholdSlider.isEnabled = settings.enableEdgeEnhancement
        edgeThresholdSlider.target = self
        edgeThresholdSlider.action = #selector(edgeThresholdChanged)
        
        edgeStack.addView(edgeCheckbox, in: .top)
        edgeStack.addView(edgeThresholdLabel, in: .top)
        edgeStack.addView(edgeThresholdSlider, in: .top)
        mainStack.addView(edgeStack, in: .top)
        
        // --- Refresh Rate (FPS) Row ---
        let fpsStack = NSStackView()
        fpsStack.orientation = .vertical
        fpsStack.alignment = .leading
        fpsStack.spacing = 6
        fpsStack.translatesAutoresizingMaskIntoConstraints = false
        
        configureLabel(fpsLabel)
        
        fpsSegmented.segmentCount = 2
        fpsSegmented.setLabel("30 FPS", forSegment: 0)
        fpsSegmented.setLabel("Native", forSegment: 1)
        fpsSegmented.selectedSegment = (settings.targetFps == 30) ? 0 : 1
        fpsSegmented.target = self
        fpsSegmented.action = #selector(fpsChanged)
        fpsSegmented.translatesAutoresizingMaskIntoConstraints = false
        
        fpsStack.addView(fpsLabel, in: .top)
        fpsStack.addView(fpsSegmented, in: .top)
        mainStack.addView(fpsStack, in: .top)
        
        // --- Neural Enhancement Row ---
        let neuralStack = NSStackView()
        neuralStack.orientation = .vertical
        neuralStack.alignment = .leading
        neuralStack.spacing = 6
        neuralStack.translatesAutoresizingMaskIntoConstraints = false
        
        neuralCheckbox.setButtonType(.switch)
        neuralCheckbox.title = "Neural Enhancement (Beta)"
        neuralCheckbox.state = settings.neuralEnhancement ? .on : .off
        neuralCheckbox.font = labelFont
        neuralCheckbox.target = self
        neuralCheckbox.action = #selector(neuralChanged)
        
        neuralStack.addView(neuralCheckbox, in: .top)
        mainStack.addView(neuralStack, in: .top)
        
        // --- Action Buttons ---
        let actionStack = NSStackView()
        actionStack.orientation = .horizontal
        actionStack.alignment = .centerY
        actionStack.spacing = 12
        actionStack.translatesAutoresizingMaskIntoConstraints = false
        
        toggleOverlayButton.title = "Pause Filter"
        toggleOverlayButton.bezelStyle = .rounded
        toggleOverlayButton.font = labelFont
        toggleOverlayButton.target = self
        toggleOverlayButton.action = #selector(togglePressed)
        toggleOverlayButton.translatesAutoresizingMaskIntoConstraints = false
        
        let quitTitle = NSAttributedString(string: "Quit", attributes: [
            .foregroundColor: NSColor.systemRed,
            .font: labelFont
        ])
        quitButton.attributedTitle = quitTitle
        quitButton.bezelStyle = .rounded
        quitButton.target = self
        quitButton.action = #selector(quitPressed)
        quitButton.translatesAutoresizingMaskIntoConstraints = false
        
        actionStack.addView(toggleOverlayButton, in: .top)
        actionStack.addView(quitButton, in: .top)
        mainStack.addView(actionStack, in: .top)
        
        // Add Stack to View
        guard let contentView = self.contentView else { return }
        contentView.addSubview(mainStack)
        
        // Set constraints to stretch stack components
        NSLayoutConstraint.activate([
            mainStack.topAnchor.constraint(equalTo: contentView.topAnchor),
            mainStack.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            mainStack.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            mainStack.bottomAnchor.constraint(equalTo: contentView.bottomAnchor),
            
            tileSizeStack.widthAnchor.constraint(equalTo: mainStack.widthAnchor, constant: -40),
            tileSizeSlider.widthAnchor.constraint(equalTo: tileSizeStack.widthAnchor),
            
            opacityStack.widthAnchor.constraint(equalTo: mainStack.widthAnchor, constant: -40),
            opacitySlider.widthAnchor.constraint(equalTo: opacityStack.widthAnchor),
            
            charSetStack.widthAnchor.constraint(equalTo: mainStack.widthAnchor, constant: -40),
            charSetPopup.widthAnchor.constraint(equalTo: charSetStack.widthAnchor),
            
            colorModeStack.widthAnchor.constraint(equalTo: mainStack.widthAnchor, constant: -40),
            colorModePopup.widthAnchor.constraint(equalTo: colorModeStack.widthAnchor),
            
            edgeStack.widthAnchor.constraint(equalTo: mainStack.widthAnchor, constant: -40),
            edgeThresholdSlider.widthAnchor.constraint(equalTo: edgeStack.widthAnchor),
            
            fpsStack.widthAnchor.constraint(equalTo: mainStack.widthAnchor, constant: -40),
            fpsSegmented.widthAnchor.constraint(equalTo: fpsStack.widthAnchor),
            
            neuralStack.widthAnchor.constraint(equalTo: mainStack.widthAnchor, constant: -40)
        ])
    }
    
    // MARK: - Actions
    
    @objc private func tileSizeChanged() {
        let value = Int(tileSizeSlider.doubleValue)
        settings.tileSize = value
        tileSizeLabel.stringValue = "Tile Size: \(value)px"
        notifyDelegate()
    }
    
    @objc private func opacityChanged() {
        let value = Float(opacitySlider.doubleValue)
        settings.opacity = value
        opacityLabel.stringValue = "ASCII Opacity: \(Int(value * 100.0))%"
        notifyDelegate()
    }
    
    @objc private func charSetChanged() {
        settings.charSetIndex = charSetPopup.indexOfSelectedItem
        notifyDelegate()
    }
    
    @objc private func colorModeChanged() {
        settings.colorMode = colorModePopup.indexOfSelectedItem
        notifyDelegate()
    }
    
    @objc private func edgeCheckboxChanged() {
        let enabled = (edgeCheckbox.state == .on)
        settings.enableEdgeEnhancement = enabled
        edgeThresholdSlider.isEnabled = enabled
        notifyDelegate()
    }
    
    @objc private func edgeThresholdChanged() {
        let value = Float(edgeThresholdSlider.doubleValue)
        settings.edgeThreshold = value
        edgeThresholdLabel.stringValue = String(format: "Edge Sensitivity: %.2f", value)
        notifyDelegate()
    }
    
    @objc private func fpsChanged() {
        let fps = (fpsSegmented.selectedSegment == 0) ? 30 : 60
        settings.targetFps = fps
        notifyDelegate()
    }
    
    @objc private func togglePressed() {
        controllerDelegate?.controllerDidToggleOverlay()
    }
    
    @objc private func quitPressed() {
        controllerDelegate?.controllerDidRequestQuit()
    }
    
    @objc private func neuralChanged() {
        settings.neuralEnhancement = (neuralCheckbox.state == .on)
        notifyDelegate()
    }
    
    private func notifyDelegate() {
        controllerDelegate?.controllerDidUpdateSettings(settings)
    }
    
    // MARK: - Public Interface
    
    func updateOverlayButtonState(isEnabled: Bool) {
        settings.isOverlayEnabled = isEnabled
        toggleOverlayButton.title = isEnabled ? "Pause Filter" : "Resume Filter"
    }
}
