import Metal
import MetalKit
import AppKit

class ASCIIFilterRenderer: NSObject, MTKViewDelegate {
    weak var view: MTKView?
    
    private let device: MTLDevice
    private let commandQueue: MTLCommandQueue
    private var classifierPipelineState: MTLComputePipelineState!
    private var renderPipelineState: MTLComputePipelineState!
    private var metadataTexture: MTLTexture?
    
    private let stateLock = NSLock()
    private var _latestScreenTexture: MTLTexture?
    
    var latestScreenTexture: MTLTexture? {
        get {
            stateLock.lock()
            defer { stateLock.unlock() }
            return _latestScreenTexture
        }
        set {
            stateLock.lock()
            _latestScreenTexture = newValue
            stateLock.unlock()
        }
    }
    
    // Character Set Definitions
    let characterSets = [
        " .:-=+*#%@",                // Standard ASCII
        " ░▒▓█",                     // Blocky Unicode
        " .':,;!~+*eom#W@",         // Extended ASCII
        " ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿ" // Retro Matrix / Katakana
    ]
    
    // Active Settings & Dynamic Resources
    private var settings = AppSettings()
    private var atlasTexture: MTLTexture?
    private var atlasCharWidth: Int = 0
    private var atlasCharHeight: Int = 0
    private var uniformsBuffer: MTLBuffer?
    private var characterWeightsBuffer: MTLBuffer?
    
    init(device: MTLDevice) {
        self.device = device
        self.commandQueue = device.makeCommandQueue()!
        super.init()
        
        setupPipeline()
        setupUniformsBuffer()
        regenerateAtlas()
    }
    
    private func setupPipeline() {
        do {
            let library = try device.makeLibrary(source: MetalShaderSource.source, options: nil)
            guard let classifierFunc = library.makeFunction(name: "tileClassifier") else {
                fatalError("Metal function 'tileClassifier' not found in source.")
            }
            guard let renderFunc = library.makeFunction(name: "asciiRender") else {
                fatalError("Metal function 'asciiRender' not found in source.")
            }
            classifierPipelineState = try device.makeComputePipelineState(function: classifierFunc)
            renderPipelineState = try device.makeComputePipelineState(function: renderFunc)
        } catch {
            fatalError("Failed to compile Metal shaders: \(error)")
        }
    }
    
    private func setupUniformsBuffer() {
        // Uniforms struct is 48 bytes (aligned to 16 bytes)
        uniformsBuffer = device.makeBuffer(length: 48, options: .storageModeShared)
    }
    
    func updateSettings(_ newSettings: AppSettings) {
        stateLock.lock()
        let charSetChanged = (settings.charSetIndex != newSettings.charSetIndex)
        let edgeEnhancementChanged = (settings.enableEdgeEnhancement != newSettings.enableEdgeEnhancement)
        self.settings = newSettings
        let needRegen = charSetChanged || edgeEnhancementChanged || atlasTexture == nil
        stateLock.unlock()
        
        if needRegen {
            regenerateAtlas()
        }
    }
    
    func updateLatestTexture(_ texture: MTLTexture) {
        stateLock.lock()
        self._latestScreenTexture = texture
        stateLock.unlock()
        
        self.view?.draw()
    }
    
    // MARK: - Dynamic Atlas Generation
    
    private func regenerateAtlas() {
        stateLock.lock()
        let charSetIndex = settings.charSetIndex
        let enableEdgeEnhancement = settings.enableEdgeEnhancement
        stateLock.unlock()
        
        var baseCharacters = characterSets[charSetIndex]
        
        // Append edge-enhancement override glyphs to the end of the atlas if enabled
        if enableEdgeEnhancement {
            baseCharacters += "|-/\\"
        }
        
        // Render characters to texture
        // Use a clean monospaced font like Menlo
        guard let atlasData = createASCIIAtlas(characters: baseCharacters, fontName: "Menlo", fontSize: 24.0) else {
            print("Error: Could not generate ASCII character atlas.")
            return
        }
        
        stateLock.lock()
        self.atlasTexture = atlasData.texture
        self.atlasCharWidth = atlasData.charWidth
        self.atlasCharHeight = atlasData.charHeight
        
        // Train dynamic classifier neural weights for each character shape
        let numChars = baseCharacters.count
        let bufferSize = numChars * 16 * MemoryLayout<Float>.size
        self.characterWeightsBuffer = device.makeBuffer(length: bufferSize, options: .storageModeShared)
        
        if let buf = self.characterWeightsBuffer {
            let pointer = buf.contents().assumingMemoryBound(to: Float.self)
            
            for c in 0..<numChars {
                var grid = [Float](repeating: 0.0, count: 16)
                
                // Downsample glyph bounds into a 4x4 weight grid
                for gy in 0..<4 {
                    for gx in 0..<4 {
                        let xStart = c * atlasData.charWidth + (gx * atlasData.charWidth) / 4
                        let xEnd = c * atlasData.charWidth + ((gx + 1) * atlasData.charWidth) / 4
                        let yStart = (gy * atlasData.charHeight) / 4
                        let yEnd = ((gy + 1) * atlasData.charHeight) / 4
                        
                        var sumLuma: Float = 0.0
                        var pixelCount: Float = 0.0
                        
                        for y in yStart..<yEnd {
                            for x in xStart..<xEnd {
                                let pixelIndex = (y * atlasData.atlasWidth + x) * 4
                                if pixelIndex + 3 < atlasData.rawData.count {
                                    let r = Float(atlasData.rawData[pixelIndex]) / 255.0
                                    let g = Float(atlasData.rawData[pixelIndex + 1]) / 255.0
                                    let b = Float(atlasData.rawData[pixelIndex + 2]) / 255.0
                                    let luma = 0.299 * r + 0.587 * g + 0.114 * b
                                    sumLuma += luma
                                    pixelCount += 1.0
                                }
                            }
                        }
                        
                        let avgCellLuma = pixelCount > 0 ? (sumLuma / pixelCount) : 0.0
                        grid[gy * 4 + gx] = avgCellLuma
                    }
                }
                
                // Standardize: subtract mean and normalize weight vector to unit length
                let mean = grid.reduce(0, +) / 16.0
                let zeroMeanGrid = grid.map { $0 - mean }
                let norm = sqrt(zeroMeanGrid.map { $0 * $0 }.reduce(0, +))
                
                if norm > 0.001 {
                    for i in 0..<16 {
                        pointer[c * 16 + i] = zeroMeanGrid[i] / norm
                    }
                } else {
                    for i in 0..<16 {
                        pointer[c * 16 + i] = 0.0
                    }
                }
            }
        }
        stateLock.unlock()
    }
    
    private func createASCIIAtlas(characters: String, fontName: String, fontSize: CGFloat) -> (texture: MTLTexture, charWidth: Int, charHeight: Int, rawData: [UInt8], atlasWidth: Int, atlasHeight: Int)? {
        let font = NSFont(name: fontName, size: fontSize) ?? NSFont.monospacedSystemFont(ofSize: fontSize, weight: .regular)
        let attributes: [NSAttributedString.Key: Any] = [
            .font: font,
            .foregroundColor: NSColor.white
        ]
        
        // Measure single glyph to calculate dimensions
        let dummySize = "M".size(withAttributes: attributes)
        let charWidth = Int(ceil(dummySize.width))
        let charHeight = Int(ceil(dummySize.height))
        
        let numChars = characters.count
        let atlasWidth = charWidth * numChars
        let atlasHeight = charHeight
        
        let bytesPerPixel = 4
        let bytesPerRow = atlasWidth * bytesPerPixel
        var rawData = [UInt8](repeating: 0, count: bytesPerRow * atlasHeight)
        
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        guard let context = CGContext(
            data: &rawData,
            width: atlasWidth,
            height: atlasHeight,
            bitsPerComponent: 8,
            bytesPerRow: bytesPerRow,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            return nil
        }
        
        // Draw into graphics context
        NSGraphicsContext.saveGraphicsState()
        let nsGraphicsContext = NSGraphicsContext(cgContext: context, flipped: false)
        NSGraphicsContext.current = nsGraphicsContext
        
        // Clear background to solid black (or clear, but black is optimal for ASCII density math)
        context.setFillColor(CGColor(red: 0, green: 0, blue: 0, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: atlasWidth, height: atlasHeight))
        
        // Draw glyphs horizontally
        for (i, char) in characters.enumerated() {
            let charStr = String(char)
            let x = CGFloat(i * charWidth)
            
            // Align characters centrally in vertical grids
            let charSize = charStr.size(withAttributes: attributes)
            let yOffset = (CGFloat(charHeight) - charSize.height) / 2.0
            
            let rect = CGRect(x: x, y: yOffset, width: CGFloat(charWidth), height: CGFloat(charHeight))
            charStr.draw(in: rect, withAttributes: attributes)
        }
        
        NSGraphicsContext.restoreGraphicsState()
        
        // Load into Metal Texture
        let textureDescriptor = MTLTextureDescriptor.texture2DDescriptor(
            pixelFormat: .rgba8Unorm,
            width: atlasWidth,
            height: atlasHeight,
            mipmapped: false
        )
        textureDescriptor.usage = [.shaderRead]
        
        guard let texture = device.makeTexture(descriptor: textureDescriptor) else {
            return nil
        }
        
        let region = MTLRegionMake2D(0, 0, atlasWidth, atlasHeight)
        texture.replace(
            region: region,
            mipmapLevel: 0,
            withBytes: rawData,
            bytesPerRow: bytesPerRow
        )
        
        return (texture, charWidth, charHeight, rawData, atlasWidth, atlasHeight)
    }
    
    // MARK: - MTKViewDelegate
    
    func mtkView(_ view: MTKView, drawableSizeWillChange size: CGSize) {
        // Handled automatically by Metal scaling logic in the compute shader.
    }
    
    func draw(in view: MTKView) {
        // Fetch currentDrawable without holding the stateLock to prevent deadlock.
        guard let drawable = view.currentDrawable else {
            return
        }
        
        stateLock.lock()
        guard let screenTex = _latestScreenTexture,
              let atlasTex = atlasTexture,
              let uniformsBuf = uniformsBuffer else {
            stateLock.unlock()
            return
        }
        
        let currentSettings = self.settings
        let currentAtlasCharWidth = self.atlasCharWidth
        let currentAtlasCharHeight = self.atlasCharHeight
        stateLock.unlock()
        
        // Configure drawable write access (framebufferOnly must be false)
        view.framebufferOnly = false
        
        // Calculate font aspect ratio to prevent scaling skew (typically 1 : 1.5)
        let tileW = UInt32(currentSettings.tileSize)
        let tileH = UInt32(currentSettings.tileSize * 3 / 2)
        
        let tilesX = (drawable.texture.width + Int(tileW) - 1) / Int(tileW)
        let tilesY = (drawable.texture.height + Int(tileH) - 1) / Int(tileH)
        
        // Allocate/resize metadata texture if needed
        if metadataTexture == nil || metadataTexture!.width != tilesX || metadataTexture!.height != tilesY {
            let desc = MTLTextureDescriptor.texture2DDescriptor(
                pixelFormat: .rgba32Float,
                width: tilesX,
                height: tilesY,
                mipmapped: false
            )
            desc.usage = [.shaderRead, .shaderWrite]
            desc.storageMode = .private
            metadataTexture = device.makeTexture(descriptor: desc)
        }
        
        // Setup Uniforms struct
        struct MetalUniforms {
            var tileWidth: UInt32
            var tileHeight: UInt32
            var atlasCharWidth: UInt32
            var atlasCharHeight: UInt32
            var numChars: UInt32
            var colorMode: UInt32
            var enableEdgeEnhancement: UInt32
            var edgeThreshold: Float
            var opacity: Float
            var neuralEnhancement: UInt32
            var outWidth: UInt32
            var outHeight: UInt32
        }
        
        let totalCharCount = UInt32(atlasTex.width / currentAtlasCharWidth)
        
        var uniforms = MetalUniforms(
            tileWidth: tileW,
            tileHeight: tileH,
            atlasCharWidth: UInt32(currentAtlasCharWidth),
            atlasCharHeight: UInt32(currentAtlasCharHeight),
            numChars: totalCharCount,
            colorMode: UInt32(currentSettings.colorMode),
            enableEdgeEnhancement: currentSettings.enableEdgeEnhancement ? 1 : 0,
            edgeThreshold: currentSettings.edgeThreshold,
            opacity: currentSettings.opacity,
            neuralEnhancement: currentSettings.neuralEnhancement ? 1 : 0,
            outWidth: UInt32(drawable.texture.width),
            outHeight: UInt32(drawable.texture.height)
        )
        
        // Copy uniforms to MTLBuffer
        let contents = uniformsBuf.contents()
        memcpy(contents, &uniforms, MemoryLayout<MetalUniforms>.size)
        
        // Encode and Dispatch
        guard let commandBuffer = commandQueue.makeCommandBuffer() else {
            return
        }
        
        // Pass 1: Tile Classifier
        if let classifierEncoder = commandBuffer.makeComputeCommandEncoder() {
            classifierEncoder.setComputePipelineState(classifierPipelineState)
            classifierEncoder.setTexture(screenTex, index: 0)
            classifierEncoder.setTexture(metadataTexture, index: 1)
            classifierEncoder.setBuffer(uniformsBuf, offset: 0, index: 0)
            if let weightsBuf = characterWeightsBuffer {
                classifierEncoder.setBuffer(weightsBuf, offset: 0, index: 1)
            }
            
            let threadGroupSize = MTLSize(width: 16, height: 16, depth: 1)
            let threadGroups = MTLSize(
                width: (tilesX + threadGroupSize.width - 1) / threadGroupSize.width,
                height: (tilesY + threadGroupSize.height - 1) / threadGroupSize.height,
                depth: 1
            )
            classifierEncoder.dispatchThreadgroups(threadGroups, threadsPerThreadgroup: threadGroupSize)
            classifierEncoder.endEncoding()
        }
        
        // Pass 2: Full-Resolution Renderer
        if let renderEncoder = commandBuffer.makeComputeCommandEncoder() {
            renderEncoder.setComputePipelineState(renderPipelineState)
            renderEncoder.setTexture(screenTex, index: 0)
            renderEncoder.setTexture(drawable.texture, index: 1)
            renderEncoder.setTexture(atlasTex, index: 2)
            renderEncoder.setTexture(metadataTexture, index: 3)
            renderEncoder.setBuffer(uniformsBuf, offset: 0, index: 0)
            
            let threadGroupSize = MTLSize(width: 16, height: 16, depth: 1)
            let threadGroups = MTLSize(
                width: (drawable.texture.width + threadGroupSize.width - 1) / threadGroupSize.width,
                height: (drawable.texture.height + threadGroupSize.height - 1) / threadGroupSize.height,
                depth: 1
            )
            renderEncoder.dispatchThreadgroups(threadGroups, threadsPerThreadgroup: threadGroupSize)
            renderEncoder.endEncoding()
        }
        
        commandBuffer.present(drawable)
        commandBuffer.commit()
    }
}
