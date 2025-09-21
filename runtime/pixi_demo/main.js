/**
 * PSD Avatar Demo - PixiJS Reference Implementation
 *
 * Demonstrates avatar animation using PSD Character Extractor bundles
 */

class AvatarPlayer {
    constructor(canvasElement) {
        this.canvas = canvasElement;
        this.app = null;
        this.avatarData = null;
        this.atlasTexture = null;
        this.sprites = {};
        this.currentState = 'IdleNeutral';
        this.isPlaying = false;
        this.blinkTimer = null;
        this.speakingAnimation = null;

        // Animation parameters
        this.params = {
            valence: 0.0,    // -1.0 to 1.0
            arousal: 0.2,    // 0.0 to 1.0
            speaking: false,
            emotion: 'neutral'
        };

        this.initPixi();
        this.setupEventListeners();
        this.startBlinkCycle();
    }

    initPixi() {
        // Create PixiJS application
        this.app = new PIXI.Application({
            view: this.canvas,
            width: 800,
            height: 600,
            backgroundColor: 0x1a1a2e,
            antialias: true
        });

        // Add to global scope for debugging
        window.__PIXI_APP__ = this.app;

        this.log('PixiJS application initialized');
    }

    async loadAvatar(avatarData, atlasBlob) {
        try {
            this.avatarData = avatarData;

            // Load atlas texture
            const atlasTexture = await PIXI.Texture.fromBuffer(
                new Uint8Array(await atlasBlob.arrayBuffer()),
                atlasBlob.name
            );
            this.atlasTexture = atlasTexture;

            // Clear existing sprites
            this.app.stage.removeChildren();
            this.sprites = {};

            // Create sprites from slices
            this.createSprites();

            // Set initial state
            this.setState('IdleNeutral');

            this.log(`Avatar loaded: ${avatarData.meta?.name || 'Unknown'}`);
            this.log(`Slots: ${Object.keys(avatarData.slots).join(', ')}`);

        } catch (error) {
            this.log(`Error loading avatar: ${error.message}`);
            throw error;
        }
    }

    createSprites() {
        if (!this.avatarData || !this.atlasTexture) return;

        const slices = this.avatarData.images.slices;
        const slots = this.avatarData.slots;

        // Group sprites by slot
        const slotSprites = {};

        for (const [sliceKey, rect] of Object.entries(slices)) {
            // Create texture from atlas slice
            const texture = new PIXI.Texture(
                this.atlasTexture.baseTexture,
                new PIXI.Rectangle(rect.x, rect.y, rect.w, rect.h)
            );

            // Create sprite
            const sprite = new PIXI.Sprite(texture);

            // Parse slice key to determine slot and state
            // Format: "Face/Eye[L]/state/open" or "Face/Mouth/viseme/AI"
            const slotInfo = this.parseSliceKey(sliceKey);

            if (slotInfo) {
                const slotName = slotInfo.slot;

                if (!slotSprites[slotName]) {
                    slotSprites[slotName] = {};
                }

                slotSprites[slotName][slotInfo.state] = sprite;

                // Position sprite (simplified positioning)
                this.positionSprite(sprite, slotName, slotInfo);

                // Initially hide all sprites
                sprite.visible = false;
                this.app.stage.addChild(sprite);
            }
        }

        this.sprites = slotSprites;
        this.log(`Created ${Object.keys(slotSprites).length} sprite slots`);
    }

    parseSliceKey(sliceKey) {
        // Parse slice keys like "Face/Eye[L]/state/open" or "Face/Mouth/viseme/AI"
        const parts = sliceKey.split('/');

        if (parts.length < 3) return null;

        // Extract slot name (e.g., "Eye[L]" -> "EyeL", "Mouth" -> "Mouth")
        let slotPart = parts[1];
        let slot = slotPart;

        // Handle bracketed sides like "Eye[L]" -> "EyeL"
        const bracketMatch = slotPart.match(/(\w+)\[([LR])\]/);
        if (bracketMatch) {
            slot = bracketMatch[1] + bracketMatch[2];
        }

        // Extract state type and value
        const stateType = parts[2];  // "state", "viseme", "emotion", "shape"
        const stateValue = parts[3]; // "open", "AI", "smile", etc.

        return {
            slot: slot,
            stateType: stateType,
            state: stateValue,
            fullKey: sliceKey
        };
    }

    positionSprite(sprite, slotName, slotInfo) {
        // Basic positioning - in a real implementation, this would use
        // anchor points and proper layout calculations

        const centerX = this.app.screen.width / 2;
        const centerY = this.app.screen.height / 2;

        // Set anchor to center
        sprite.anchor.set(0.5, 0.5);

        // Position based on slot type
        if (slotName.startsWith('Eye')) {
            sprite.y = centerY - 50;
            if (slotName.includes('L')) {
                sprite.x = centerX - 40;
            } else {
                sprite.x = centerX + 40;
            }
        } else if (slotName === 'Mouth') {
            sprite.x = centerX;
            sprite.y = centerY + 30;
        } else if (slotName.startsWith('Brow')) {
            sprite.y = centerY - 80;
            if (slotName.includes('L')) {
                sprite.x = centerX - 40;
            } else {
                sprite.x = centerX + 40;
            }
        } else {
            // Default position
            sprite.x = centerX;
            sprite.y = centerY;
        }
    }

    setState(stateName) {
        if (!this.avatarData || !this.sprites) return;

        this.currentState = stateName;

        // Define state configurations
        const stateConfigs = {
            'IdleNeutral': {
                'EyeL': { type: 'state', value: 'open' },
                'EyeR': { type: 'state', value: 'open' },
                'Mouth': { type: 'viseme', value: 'REST' }
            },
            'IdleBlink': {
                'EyeL': { type: 'state', value: 'closed' },
                'EyeR': { type: 'state', value: 'closed' },
                'Mouth': { type: 'viseme', value: 'REST' }
            },
            'TalkNeutral': {
                'EyeL': { type: 'state', value: 'open' },
                'EyeR': { type: 'state', value: 'open' },
                'Mouth': { type: 'viseme', value: 'AUTO' }
            },
            'Smile': {
                'EyeL': { type: 'state', value: 'happy' },
                'EyeR': { type: 'state', value: 'happy' },
                'Mouth': { type: 'emotion', value: 'smile' },
                'BrowL': { type: 'shape', value: 'up' },
                'BrowR': { type: 'shape', value: 'up' }
            },
            'Sad': {
                'EyeL': { type: 'state', value: 'sad' },
                'EyeR': { type: 'state', value: 'sad' },
                'Mouth': { type: 'emotion', value: 'sad' }
            },
            'Surprised': {
                'EyeL': { type: 'state', value: 'open' },
                'EyeR': { type: 'state', value: 'open' },
                'Mouth': { type: 'viseme', value: 'O' },
                'BrowL': { type: 'shape', value: 'up' },
                'BrowR': { type: 'shape', value: 'up' }
            }
        };

        const config = stateConfigs[stateName];
        if (!config) return;

        // Hide all sprites first
        this.hideAllSprites();

        // Show sprites for current state
        for (const [slotName, slotConfig] of Object.entries(config)) {
            this.showSlotState(slotName, slotConfig.type, slotConfig.value);
        }

        this.log(`State changed to: ${stateName}`);
    }

    hideAllSprites() {
        for (const slotSprites of Object.values(this.sprites)) {
            for (const sprite of Object.values(slotSprites)) {
                sprite.visible = false;
            }
        }
    }

    showSlotState(slotName, stateType, stateValue) {
        const slotSprites = this.sprites[slotName];
        if (!slotSprites) return;

        // Handle AUTO viseme (don't change if currently speaking)
        if (stateType === 'viseme' && stateValue === 'AUTO') {
            if (!this.params.speaking) {
                stateValue = 'REST';
            } else {
                return; // Keep current mouth state when speaking
            }
        }

        const sprite = slotSprites[stateValue];
        if (sprite) {
            sprite.visible = true;
        } else {
            // Fallback to first available state
            const fallbackSprite = Object.values(slotSprites)[0];
            if (fallbackSprite) {
                fallbackSprite.visible = true;
            }
        }
    }

    setViseme(viseme) {
        if (viseme === 'AUTO') return;

        this.showSlotState('Mouth', 'viseme', viseme);
        this.log(`Viseme: ${viseme}`);
    }

    startSpeaking(text) {
        this.params.speaking = true;
        this.setState('TalkNeutral');

        // Simple text-to-viseme simulation
        this.animateSpeech(text);

        this.log(`Speaking: "${text}"`);
    }

    stopSpeaking() {
        this.params.speaking = false;

        if (this.speakingAnimation) {
            clearInterval(this.speakingAnimation);
            this.speakingAnimation = null;
        }

        this.setState('IdleNeutral');
        this.log('Stopped speaking');
    }

    animateSpeech(text) {
        if (this.speakingAnimation) {
            clearInterval(this.speakingAnimation);
        }

        // Simple viseme cycling based on text
        const visemes = this.textToVisemes(text);
        let visemeIndex = 0;

        this.speakingAnimation = setInterval(() => {
            if (visemeIndex >= visemes.length) {
                this.stopSpeaking();
                return;
            }

            const viseme = visemes[visemeIndex];
            this.setViseme(viseme);
            visemeIndex++;

        }, 200); // 200ms per viseme (5 fps)
    }

    textToVisemes(text) {
        // Very basic text-to-viseme conversion for demo
        const visemes = [];
        const words = text.toLowerCase().split(' ');

        for (const word of words) {
            for (const char of word) {
                if ('aeiou'.includes(char)) {
                    if ('ai'.includes(char)) {
                        visemes.push('AI');
                    } else if (char === 'e') {
                        visemes.push('E');
                    } else if (char === 'u') {
                        visemes.push('U');
                    } else if (char === 'o') {
                        visemes.push('O');
                    }
                } else if ('fv'.includes(char)) {
                    visemes.push('FV');
                } else if (char === 'l') {
                    visemes.push('L');
                } else if ('wr'.includes(char)) {
                    visemes.push('WQ');
                } else if ('mbp'.includes(char)) {
                    visemes.push('MBP');
                } else {
                    visemes.push('REST');
                }
            }
            visemes.push('REST'); // Pause between words
        }

        return visemes;
    }

    startBlinkCycle() {
        const blink = () => {
            if (!document.getElementById('auto-blink').checked) {
                this.blinkTimer = setTimeout(blink, 2000);
                return;
            }

            if (this.currentState === 'IdleNeutral' && !this.params.speaking) {
                // Quick blink
                this.setState('IdleBlink');
                setTimeout(() => {
                    if (this.currentState === 'IdleBlink') {
                        this.setState('IdleNeutral');
                    }
                }, 150);
            }

            // Random interval 2-6 seconds
            const interval = 2000 + Math.random() * 4000;
            this.blinkTimer = setTimeout(blink, interval);
        };

        blink();
    }

    updateParams(params) {
        Object.assign(this.params, params);
        this.log(`Params updated: valence=${this.params.valence.toFixed(2)}, arousal=${this.params.arousal.toFixed(2)}`);
    }

    setupEventListeners() {
        // Expression control
        document.getElementById('expression-select').addEventListener('change', (e) => {
            this.setState(e.target.value);
        });

        // Manual viseme control
        document.getElementById('viseme-select').addEventListener('change', (e) => {
            if (e.target.value !== 'AUTO') {
                this.setViseme(e.target.value);
            }
        });

        // Emotion sliders
        const valenceSlider = document.getElementById('valence-slider');
        const arousalSlider = document.getElementById('arousal-slider');

        valenceSlider.addEventListener('input', (e) => {
            const value = parseInt(e.target.value) / 100;
            document.getElementById('valence-value').textContent = value.toFixed(2);
            this.updateParams({ valence: value });
        });

        arousalSlider.addEventListener('input', (e) => {
            const value = parseInt(e.target.value) / 100;
            document.getElementById('arousal-value').textContent = value.toFixed(2);
            this.updateParams({ arousal: value });
        });

        // Speech controls
        document.getElementById('speak-button').addEventListener('click', () => {
            const text = document.getElementById('speech-text').value;
            if (text.trim()) {
                this.startSpeaking(text);
                document.getElementById('speak-button').disabled = true;
                document.getElementById('stop-button').disabled = false;
            }
        });

        document.getElementById('stop-button').addEventListener('click', () => {
            this.stopSpeaking();
            document.getElementById('speak-button').disabled = false;
            document.getElementById('stop-button').disabled = true;
        });

        // File uploads
        document.getElementById('avatar-file').addEventListener('change', (e) => {
            if (e.target.files[0]) {
                window.avatarFile = e.target.files[0];
                this.tryLoadAvatar();
            }
        });

        document.getElementById('atlas-file').addEventListener('change', (e) => {
            if (e.target.files[0]) {
                window.atlasFile = e.target.files[0];
                this.tryLoadAvatar();
            }
        });
    }

    async tryLoadAvatar() {
        if (window.avatarFile && window.atlasFile) {
            try {
                const avatarText = await window.avatarFile.text();
                const avatarData = JSON.parse(avatarText);

                await this.loadAvatar(avatarData, window.atlasFile);

            } catch (error) {
                this.log(`Error loading files: ${error.message}`);
            }
        }
    }

    log(message) {
        const statusLog = document.getElementById('status-log');
        const timestamp = new Date().toLocaleTimeString();
        statusLog.innerHTML += `<div>[${timestamp}] ${message}</div>`;
        statusLog.scrollTop = statusLog.scrollHeight;
    }
}

// Initialize the avatar player when the page loads
let avatarPlayer = null;

document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('avatar-canvas');
    avatarPlayer = new AvatarPlayer(canvas);

    // Make globally available for debugging
    window.avatarPlayer = avatarPlayer;
});

// Resize handler
window.addEventListener('resize', () => {
    if (avatarPlayer && avatarPlayer.app) {
        const container = document.querySelector('.canvas-container');
        const rect = container.getBoundingClientRect();
        avatarPlayer.app.renderer.resize(rect.width - 40, rect.height - 40);
    }
});