import ScreenCaptureKit
import CoreMedia
import Metal

class ScreenCaptureManager: NSObject, SCStreamOutput, SCStreamDelegate {
    private let device: MTLDevice
    private var stream: SCStream?
    private var textureCache: CVMetalTextureCache?
    
    var onFrameCaptured: ((MTLTexture) -> Void)?
    
    init(device: MTLDevice) {
        self.device = device
        super.init()
        setupTextureCache()
    }
    
    private func setupTextureCache() {
        let status = CVMetalTextureCacheCreate(kCFAllocatorDefault, nil, device, nil, &textureCache)
        if status != kCVReturnSuccess {
            print("Failed to create Metal texture cache: \(status)")
        }
    }
    
    func startCapture(excluding windows: [SCWindow], targetFps: Int) {
        // Stop any active stream before starting a new one
        if stream != nil {
            stream?.stopCapture { [weak self] _ in
                self?.stream = nil
                self?.startCaptureInternal(excluding: windows, targetFps: targetFps)
            }
        } else {
            startCaptureInternal(excluding: windows, targetFps: targetFps)
        }
    }
    
    private func startCaptureInternal(excluding windows: [SCWindow], targetFps: Int) {
        SCShareableContent.getWithCompletionHandler { [weak self] content, error in
            guard let self = self else { return }
            guard let content = content, error == nil else {
                print("Failed to get shareable content: \(String(describing: error))")
                return
            }
            
            guard let display = content.displays.first else {
                print("No displays available.")
                return
            }
            
            // Re-evaluate list to filter windows from our own PID to prevent loops
            let myPid = ProcessInfo.processInfo.processIdentifier
            let excludeWindows = content.windows.filter { $0.owningApplication?.processID == myPid }
            
            let filter = SCContentFilter(display: display, excludingWindows: excludeWindows)
            let config = SCStreamConfiguration()
            
            // Target the display bounds exactly
            config.width = Int(display.width)
            config.height = Int(display.height)
            config.pixelFormat = kCVPixelFormatType_32BGRA
            config.queueDepth = 2
            config.showsCursor = true
            config.minimumFrameInterval = CMTime(value: 1, timescale: CMTimeScale(targetFps))
            
            let newStream = SCStream(filter: filter, configuration: config, delegate: self)
            self.stream = newStream
            
            do {
                let captureQueue = DispatchQueue(label: "com.antigravity.capture.queue", qos: .userInteractive)
                try newStream.addStreamOutput(self, type: .screen, sampleHandlerQueue: captureQueue)
                
                newStream.startCapture { error in
                    if let error = error {
                        print("Failed to start stream capture: \(error)")
                    } else {
                        print("Stream capture started successfully.")
                    }
                }
            } catch {
                print("Failed to add stream output: \(error)")
            }
        }
    }
    
    func stopCapture() {
        guard let activeStream = stream else { return }
        activeStream.stopCapture { [weak self] error in
            if let error = error {
                print("Failed to stop stream capture: \(error)")
            } else {
                print("Stream capture stopped.")
            }
            self?.stream = nil
        }
    }
    
    func updateFps(_ fps: Int) {
        guard let activeStream = stream else { return }
        
        SCShareableContent.getWithCompletionHandler { content, error in
            guard let content = content, error == nil else { return }
            guard let display = content.displays.first else { return }
            
            let config = SCStreamConfiguration()
            config.width = Int(display.width)
            config.height = Int(display.height)
            config.pixelFormat = kCVPixelFormatType_32BGRA
            config.queueDepth = 2
            config.showsCursor = true
            config.minimumFrameInterval = CMTime(value: 1, timescale: CMTimeScale(fps))
            
            activeStream.updateConfiguration(config) { error in
                if let error = error {
                    print("Failed to update stream configuration: \(error)")
                } else {
                    print("Stream capture configuration updated dynamically (FPS: \(fps)).")
                }
            }
        }
    }
    
    // MARK: - SCStreamOutput
    
    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer, of type: SCStreamOutputType) {
        autoreleasepool {
            guard type == .screen else { return }
            guard let imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
            guard let cache = textureCache else { return }
            
            let width = CVPixelBufferGetWidth(imageBuffer)
            let height = CVPixelBufferGetHeight(imageBuffer)
            
            var cvTexture: CVMetalTexture?
            let status = CVMetalTextureCacheCreateTextureFromImage(
                kCFAllocatorDefault,
                cache,
                imageBuffer,
                nil,
                .bgra8Unorm,
                width,
                height,
                0,
                &cvTexture
            )
            
            if status == kCVReturnSuccess, let cvTex = cvTexture {
                if let metalTexture = CVMetalTextureGetTexture(cvTex) {
                    onFrameCaptured?(metalTexture)
                }
            }
        }
    }
    
    // MARK: - SCStreamDelegate
    
    func stream(_ stream: SCStream, didStopWithError error: Error) {
        print("Stream stopped with error: \(error)")
    }
}
