import Foundation

struct MetalShaderSource {
    static let source = """
    #include <metal_stdlib>
    using namespace metal;

    struct Uniforms {
        uint tileWidth;
        uint tileHeight;
        uint atlasCharWidth;
        uint atlasCharHeight;
        uint numChars;
        uint colorMode;
        uint enableEdgeEnhancement;
        float edgeThreshold;
        float opacity;
        uint neuralEnhancement;
        uint outWidth;
        uint outHeight;
    };

    // Convert sRGB color component to linear space
    float3 srgbToLinear(float3 srgb) {
        return pow(max(srgb, 0.0), 2.2);
    }

    // Convert linear space color back to sRGB space
    float linearToSrgb(float lin) {
        return pow(max(lin, 0.0), 1.0 / 2.2);
    }

    // Physically accurate luminance math based on human perception
    float getLuminance(float3 srgbColor) {
        float3 linColor = srgbToLinear(srgbColor);
        float linLuma = dot(linColor, float3(0.2126, 0.7152, 0.0722));
        return linearToSrgb(linLuma);
    }

    struct NeuralEnhancement {
        float2 offset;
        float4 colorMultiplier;
    };

    inline NeuralEnhancement runNeuralEnhancer(
        texture2d<float, access::sample> inTex,
        sampler s,
        float2 uv,
        float2 texelSize
    ) {
        float3 samples[9];
        #pragma unroll
        for (int y = -1; y <= 1; ++y) {
            #pragma unroll
            for (int x = -1; x <= 1; ++x) {
                float2 offsetUV = float2(x, y) * texelSize * 2.0;
                samples[(y+1)*3 + (x+1)] = inTex.sample(s, uv + offsetUV).rgb;
            }
        }
        
        float luma[9];
        #pragma unroll
        for (int i = 0; i < 9; ++i) {
            luma[i] = dot(samples[i], float3(0.299, 0.587, 0.114));
        }
        
        float w1[9] = { -1, 0, 1, -2, 0, 2, -1, 0, 1 };
        float w2[9] = { -1, -2, -1, 0, 0, 0, 1, 2, 1 };
        float w3[9] = { 0, -1, 0, -1, 4, -1, 0, -1, 0 };
        
        float h1 = 0;
        float h2 = 0;
        float h3 = 0;
        #pragma unroll
        for (int i = 0; i < 9; ++i) {
            h1 += luma[i] * w1[i];
            h2 += luma[i] * w2[i];
            h3 += luma[i] * w3[i];
        }
        
        h1 = max(h1, 0.0);
        h2 = max(h2, 0.0);
        h3 = max(h3, 0.0);
        
        float dx = (h1 - h2) * 0.02;
        float dy = (h2 - h1) * 0.02;
        
        float colorBoost = 1.0 + h3 * 0.5;
        colorBoost = clamp(colorBoost, 0.9, 1.6);
        
        NeuralEnhancement out;
        out.offset = float2(dx, dy);
        out.colorMultiplier = float4(colorBoost, colorBoost, colorBoost, 1.0);
        return out;
    }

    // PASS 1: Tile Classifier (runs per tile in a low-resolution grid)
    kernel void tileClassifier(
        texture2d<float, access::sample> inTexture [[texture(0)]],
        texture2d<float, access::write> tileMetadata [[texture(1)]],
        constant Uniforms& uniforms [[buffer(0)]],
        constant float* charWeights [[buffer(1)]],
        uint2 gid [[thread_position_in_grid]]
    ) {
        uint tilesX = tileMetadata.get_width();
        uint tilesY = tileMetadata.get_height();
        if (gid.x >= tilesX || gid.y >= tilesY) return;

        uint inW = inTexture.get_width();
        uint inH = inTexture.get_height();
        
        uint tileWidth = uniforms.tileWidth;
        uint tileHeight = uniforms.tileHeight;
        uint outW = uniforms.outWidth;
        uint outH = uniforms.outHeight;
        
        // Scale factors to map output coordinates to input coordinate space
        float scaleX = float(inW) / float(outW);
        float scaleY = float(inH) / float(outH);
        
        // Calculate tile boundaries in output space
        uint outTileStartX = gid.x * tileWidth;
        uint outTileStartY = gid.y * tileHeight;
        
        // Map to input coordinates
        uint inTileStartX = uint(float(outTileStartX) * scaleX);
        uint inTileStartY = uint(float(outTileStartY) * scaleY);
        uint inTileWidth = uint(float(tileWidth) * scaleX);
        uint inTileHeight = uint(float(tileHeight) * scaleY);
        
        // Calculate tile center in input pixel space
        float tileCenterInX = float(inTileStartX) + float(inTileWidth) * 0.5;
        float tileCenterInY = float(inTileStartY) + float(inTileHeight) * 0.5;
        float2 tileCenterUV = float2(tileCenterInX / float(inW), tileCenterInY / float(inH));
        
        // Use a constexpr bilinear sampler for fast hardware texture downsampling
        constexpr sampler textureSampler(coord::normalized, filter::linear, address::clamp_to_edge);
        
        // Neural Network Enhancement (CNN)
        float2 offset = float2(0.0);
        float colorBoost = 1.0;
        if (uniforms.neuralEnhancement != 0) {
            float2 texelSize = float2(1.0 / float(inW), 1.0 / float(inH));
            NeuralEnhancement ne = runNeuralEnhancer(inTexture, textureSampler, tileCenterUV, texelSize);
            tileCenterUV += ne.offset;
            offset = ne.offset;
            colorBoost = ne.colorMultiplier.r;
        }
        
        // Get Average Color of the input tile using hardware linear filtering
        float4 avgColor = inTexture.sample(textureSampler, tileCenterUV);
        float avgLuma = getLuminance(avgColor.rgb);
        
        // Sobel Edge Detection / Character Overrides (Used in standard mode)
        int edgeCharIndex = -1;
        if (uniforms.enableEdgeEnhancement != 0) {
            float stepX = float(inTileWidth) / float(inW);
            float stepY = float(inTileHeight) / float(inH);
            
            float L_l  = getLuminance(inTexture.sample(textureSampler, tileCenterUV + float2(-1.0 * stepX,  0.0 * stepY)).rgb);
            float L_r  = getLuminance(inTexture.sample(textureSampler, tileCenterUV + float2( 1.0 * stepX,  0.0 * stepY)).rgb);
            float L_t  = getLuminance(inTexture.sample(textureSampler, tileCenterUV + float2( 0.0 * stepX, -1.0 * stepY)).rgb);
            float L_b  = getLuminance(inTexture.sample(textureSampler, tileCenterUV + float2( 0.0 * stepX,  1.0 * stepY)).rgb);
            float L_tl = getLuminance(inTexture.sample(textureSampler, tileCenterUV + float2(-1.0 * stepX, -1.0 * stepY)).rgb);
            float L_tr = getLuminance(inTexture.sample(textureSampler, tileCenterUV + float2( 1.0 * stepX, -1.0 * stepY)).rgb);
            float L_bl = getLuminance(inTexture.sample(textureSampler, tileCenterUV + float2(-1.0 * stepX,  1.0 * stepY)).rgb);
            float L_br = getLuminance(inTexture.sample(textureSampler, tileCenterUV + float2( 1.0 * stepX,  1.0 * stepY)).rgb);
            
            // Sobel kernels
            float gx = (L_tr + 2.0 * L_r + L_br) - (L_tl + 2.0 * L_l + L_bl);
            float gy = (L_bl + 2.0 * L_b + L_br) - (L_tl + 2.0 * L_t + L_tr);
            float edgeMag = sqrt(gx * gx + gy * gy);
            
            if (edgeMag > uniforms.edgeThreshold) {
                float angle = atan2(gy, gx); // -PI to PI
                float deg = angle * 180.0 / 3.14159265;
                if (deg < 0.0) deg += 360.0;
                
                // Map edge angles to specific characters appended to the end of the atlas texture.
                // Index 0: '|', Index 1: '-', Index 2: '/', Index 3: '\'
                uint baseCharCount = uniforms.enableEdgeEnhancement != 0 ? uniforms.numChars - 4 : uniforms.numChars;
                if (deg >= 337.5 || deg < 22.5 || (deg >= 157.5 && deg < 202.5)) {
                    edgeCharIndex = int(baseCharCount) + 0; // '|'
                } else if ((deg >= 67.5 && deg < 112.5) || (deg >= 247.5 && deg < 292.5)) {
                    edgeCharIndex = int(baseCharCount) + 1; // '-'
                } else if ((deg >= 22.5 && deg < 67.5) || (deg >= 202.5 && deg < 247.5)) {
                    edgeCharIndex = int(baseCharCount) + 3; // '\'
                } else {
                    edgeCharIndex = int(baseCharCount) + 2; // '/'
                }
            }
        }
        
        // Pick active character index using 4x4 classifier if neural enhancement is enabled
        int charIndex = 0;
        if (edgeCharIndex >= 0) {
            charIndex = edgeCharIndex;
        } else if (uniforms.neuralEnhancement != 0) {
            // Extract the 4x4 structural neighborhood from input image tile
            float localLuma[16];
            #pragma unroll
            for (int gy = 0; gy < 4; ++gy) {
                #pragma unroll
                for (int gx = 0; gx < 4; ++gx) {
                    float cellX = float(inTileStartX) + float(inTileWidth) * (float(gx) + 0.5f) / 4.0f;
                    float cellY = float(inTileStartY) + float(inTileHeight) * (float(gy) + 0.5f) / 4.0f;
                    float2 cellUV = float2(cellX / float(inW), cellY / float(inH));
                    
                    float4 color = inTexture.sample(textureSampler, cellUV);
                    localLuma[gy * 4 + gx] = getLuminance(color.rgb);
                }
            }
            
            // Standardize local features (zero-mean and normalization) to match weights formatting
            float mean = 0.0f;
            #pragma unroll
            for (int i = 0; i < 16; ++i) {
                mean += localLuma[i];
            }
            mean /= 16.0f;
            
            float norm = 0.0f;
            float zeroMeanLuma[16];
            #pragma unroll
            for (int i = 0; i < 16; ++i) {
                zeroMeanLuma[i] = localLuma[i] - mean;
                norm += zeroMeanLuma[i] * zeroMeanLuma[i];
            }
            norm = sqrt(norm);
            
            if (norm > 0.001f) {
                #pragma unroll
                for (int i = 0; i < 16; ++i) {
                    zeroMeanLuma[i] /= norm;
                }
            }
            
            // Perceptron classification: pick character with maximum correlation score
            int bestCharIndex = 0;
            float bestScore = -1e9f;
            for (uint c = 0; c < uniforms.numChars; ++c) {
                float score = 0.0f;
                #pragma unroll
                for (int i = 0; i < 16; ++i) {
                    score += zeroMeanLuma[i] * charWeights[c * 16 + i];
                }
                if (score > bestScore) {
                    bestScore = score;
                    bestCharIndex = c;
                }
            }
            charIndex = bestCharIndex;
        } else {
            // Map luminance (0..1) to character index in standard array
            uint baseCharCount = uniforms.enableEdgeEnhancement != 0 ? uniforms.numChars - 4 : uniforms.numChars;
            float scaledLuma = avgLuma * float(baseCharCount);
            charIndex = clamp(int(scaledLuma), 0, int(baseCharCount) - 1);
        }
        
        // Write classification outputs to metadata texture:
        // R = charIndex (cast to float)
        // G = avgLuma
        // B = colorBoost
        // A = unused
        tileMetadata.write(float4(float(charIndex), avgLuma, colorBoost, 0.0), gid);
    }

    // PASS 2: Full-Resolution Renderer (runs per output pixel)
    kernel void asciiRender(
        texture2d<float, access::sample> inTexture [[texture(0)]],
        texture2d<float, access::write> outTexture [[texture(1)]],
        texture2d<float, access::read> asciiAtlas [[texture(2)]],
        texture2d<float, access::read> tileMetadata [[texture(3)]],
        constant Uniforms& uniforms [[buffer(0)]],
        uint2 gid [[thread_position_in_grid]]
    ) {
        uint outW = outTexture.get_width();
        uint outH = outTexture.get_height();
        if (gid.x >= outW || gid.y >= outH) return;

        uint inW = inTexture.get_width();
        uint inH = inTexture.get_height();
        
        // Scale factors to map output coordinates to input coordinate space (for Retina displays)
        float scaleX = float(inW) / float(outW);
        float scaleY = float(inH) / float(outH);
        
        uint inX = uint(float(gid.x) * scaleX);
        uint inY = uint(float(gid.y) * scaleY);
        
        uint tileWidth = uniforms.tileWidth;
        uint tileHeight = uniforms.tileHeight;
        
        // Calculate the tile coordinate
        uint tileX = gid.x / tileWidth;
        uint tileY = gid.y / tileHeight;
        
        // Read pre-computed tile metadata
        float4 metadata = tileMetadata.read(uint2(tileX, tileY));
        uint charIndex = uint(metadata.r);
        float avgLuma = metadata.g;
        float colorBoost = metadata.b;
        
        // Sample from ASCII Atlas
        uint localX = gid.x % tileWidth;
        uint localY = gid.y % tileHeight;
        
        uint atlasCharWidth = uniforms.atlasCharWidth;
        uint atlasCharHeight = uniforms.atlasCharHeight;
        
        uint atlasX = charIndex * atlasCharWidth + (localX * atlasCharWidth) / tileWidth;
        uint atlasY = (localY * atlasCharHeight) / tileHeight;
        
        float4 atlasPixel = asciiAtlas.read(uint2(atlasX, atlasY));
        float charIntensity = atlasPixel.r; // Font rendering yields grayscale intensity
        
        // Colorization options
        float4 finalColor = float4(0.0);
        float4 srcColor = inTexture.read(uint2(inX, inY));
        
        if (uniforms.colorMode == 0) {
            // Full Color Mode
            finalColor = charIntensity * srcColor;
        } else if (uniforms.colorMode == 1) {
            // Matrix Green
            float3 matrixGreen = float3(0.0, 1.0, 0.2);
            finalColor = float4(matrixGreen * charIntensity * (avgLuma * 0.8 + 0.2), 1.0);
        } else if (uniforms.colorMode == 2) {
            // Retro Amber
            float3 amberColor = float3(1.0, 0.6, 0.0);
            finalColor = float4(amberColor * charIntensity * (avgLuma * 0.8 + 0.2), 1.0);
        } else {
            // Monochrome White
            finalColor = float4(float3(charIntensity), 1.0);
        }
        
        // Apply Neural Color Multiplier (Boost detail contrast)
        finalColor *= colorBoost;
        
        // Alpha blending with the original screen capture
        float4 blendedColor = mix(srcColor, finalColor, uniforms.opacity);
        
        outTexture.write(blendedColor, gid);
    }
    """
}
