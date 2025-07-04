#!/usr/bin/env python3

print("=== New Animation Logic Trace ===\n")

# P-61_FROS has 6 frames
frame_count = 6

print("CSS: background-size: 600% auto")
print("JavaScript: percentage = (currentFrame / frameCount) * 100")
print("CSS: backgroundPosition = `-${percentage}% 0`")
print()

print("Frame-by-Frame Animation:")
for frame in range(frame_count):
    percentage = (frame / frame_count) * 100
    print(f"  Frame {frame}:")
    print(f"    currentFrame = {frame}")
    print(f"    percentage = ({frame} / {frame_count}) × 100 = {percentage:.1f}%")
    print(f"    backgroundPosition = '-{percentage:.1f}% 0'")
    print(f"    Shows frame {frame + 1} of 6")
    print()

print("Expected Results:")
print("  Frame 0: 0% → Shows Chapter 1 (leftmost frame)")
print("  Frame 1: 16.7% → Shows Chapter 2") 
print("  Frame 2: 33.3% → Shows Chapter 3")
print("  Frame 3: 50.0% → Shows Chapter 4")
print("  Frame 4: 66.7% → Shows Chapter 5")
print("  Frame 5: 83.3% → Shows Chapter 6")
print()
print("How it works:")
print("- background-size: 600% makes the sprite 6× the container width")
print("- Each frame is 1/6 of the sprite = 16.67% of the scaled sprite")
print("- Moving by 16.67% reveals the next frame exactly")