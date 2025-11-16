# Virtual Try-On Examples

This folder contains example image pairs that help improve the virtual try-on results using few-shot learning with Veo 2.

## Folder Structure

```
tryon_examples/
├── input/          # Original hand photos (before try-on)
└── output/         # Hand photos with jewelry overlaid (after try-on)
```

## Naming Convention

Files should be named with matching prefixes to pair input/output:

**Example 1 - Ring on index finger:**
- `input/example_01_hand.jpg` - Photo of hand
- `output/example_01_result.jpg` - Same hand with ring overlay

**Example 2 - Necklace:**
- `input/example_02_neck.jpg` - Photo of neck/chest area
- `output/example_02_result.jpg` - Same photo with necklace overlay

**Example 3 - Bracelet:**
- `input/example_03_wrist.jpg` - Photo of wrist
- `output/example_03_result.jpg` - Same wrist with bracelet overlay

## Image Requirements

### Input Images
- **Format**: JPG, PNG, or WEBP
- **Resolution**: Minimum 512x512, recommended 1024x1024
- **Content**: Clear, well-lit photos showing:
  - Full hand/wrist for rings/bracelets
  - Neck/chest area for necklaces
  - Ears for earrings
- **Lighting**: Consistent, natural lighting preferred
- **Background**: Any, but plain backgrounds work best

### Output Images
- **Same format** and **same resolution** as input
- **Overlay quality**: Jewelry should look naturally placed
- **Realistic**: Proper shadows, reflections, and perspective
- **Finger position**: Match the exact hand position from input

## Best Practices

1. **Pair Consistency**: Each input must have exactly one matching output
2. **Variety**: Include different:
   - Hand positions (open palm, fist, side view)
   - Skin tones
   - Lighting conditions
   - Jewelry types (rings, bracelets, necklaces, earrings)
3. **Quality**: Use high-quality, non-blurry images
4. **Realism**: Output should show jewelry naturally integrated (not just pasted on)

## How It Works

When generating virtual try-on images, the system:

1. **Scans this folder** for matching input/output pairs
2. **Loads examples** to understand the transformation pattern
3. **Uses few-shot learning** with Veo 2 to apply similar transformations
4. **Generates realistic** jewelry overlays based on learned patterns

## Adding New Examples

1. Take a clear photo of a hand/wrist/neck (save to `input/`)
2. Create a realistic overlay with jewelry (save to `output/`)
3. Use matching names with same prefix
4. Restart the backend to load new examples

## Current Status

- **Examples loaded**: 0
- **Add your own examples** to improve try-on quality!

---

**Note**: More examples = better results! Aim for at least 5-10 high-quality pairs for best performance.
