#!/usr/bin/env python3

import subprocess
import os
import sys
import requests
import re

def check_available_tools():
    """Check what tools are available for real frame extraction"""
    
    print("=== Investigating Frame Extraction Tools ===\n")
    
    tools = {
        'ffmpeg': 'ffmpeg',
        'yt-dlp': 'yt-dlp', 
        'youtube-dl': 'youtube-dl',
        'curl': 'curl',
        'wget': 'wget'
    }
    
    available_tools = {}
    
    for tool_name, command in tools.items():
        try:
            result = subprocess.run(['which', command], capture_output=True, text=True)
            if result.returncode == 0:
                path = result.stdout.strip()
                available_tools[tool_name] = path
                print(f"✅ {tool_name}: {path}")
                
                # Get version info
                try:
                    version_result = subprocess.run([command, '--version'], capture_output=True, text=True, timeout=5)
                    if version_result.returncode == 0:
                        first_line = version_result.stdout.split('\n')[0]
                        print(f"   Version: {first_line}")
                except:
                    pass
            else:
                print(f"❌ {tool_name}: Not available")
        except Exception as e:
            print(f"❌ {tool_name}: Error checking - {e}")
        
        print()
    
    return available_tools

def test_youtube_storyboard_api():
    """Test if we can access YouTube's storyboard thumbnails"""
    
    print("=== Testing YouTube Storyboard API ===\n")
    
    test_video_id = "brPYVHx8rhw"  # P-61_FROS
    
    # YouTube sometimes provides storyboard images that contain multiple frames
    storyboard_urls = [
        f"https://i.ytimg.com/sb/{test_video_id}/storyboard3_L$L/$N.jpg",
        f"https://i.ytimg.com/sb/{test_video_id}/M$M.jpg",
        f"https://i.ytimg.com/sb/{test_video_id}/default.jpg"
    ]
    
    print(f"Testing storyboard URLs for video: {test_video_id}")
    
    for url_template in storyboard_urls:
        print(f"\n🔍 Testing: {url_template}")
        
        # Try a few variations
        test_urls = [
            url_template.replace('$L', '0').replace('$N', '0').replace('$M', '0'),
            url_template.replace('$L', '1').replace('$N', '0').replace('$M', '1'),
            url_template.replace('$L', '2').replace('$N', '1').replace('$M', '2'),
        ]
        
        for test_url in test_urls:
            try:
                response = requests.head(test_url, timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ Found: {test_url}")
                    print(f"      Content-Type: {response.headers.get('content-type', 'unknown')}")
                    print(f"      Content-Length: {response.headers.get('content-length', 'unknown')} bytes")
                else:
                    print(f"   ❌ {response.status_code}: {test_url}")
            except Exception as e:
                print(f"   ❌ Error: {test_url} - {e}")

def investigate_youtube_data():
    """Try to extract more metadata from YouTube page"""
    
    print(f"\n=== Investigating YouTube Video Data ===\n")
    
    test_video_id = "brPYVHx8rhw"
    url = f"https://www.youtube.com/watch?v={test_video_id}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        content = response.text
        
        # Look for storyboard or thumbnail data
        patterns = [
            r'"storyboards":\s*({[^}]+})',
            r'"playerMicroformatRenderer":\s*({[^}]+})',
            r'"videoDetails":\s*({[^}]+})',
            r'"lengthSeconds":"(\d+)"',
        ]
        
        print(f"Searching YouTube page for metadata patterns...")
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            if matches:
                print(f"✅ Found pattern: {pattern}")
                print(f"   Matches: {len(matches)}")
                if len(matches) > 0:
                    print(f"   Sample: {str(matches[0])[:200]}...")
                print()
        
        # Look specifically for thumbnail or frame data
        if 'storyboard' in content.lower():
            print("✅ Found 'storyboard' references in page")
        if 'thumbnail' in content.lower():
            print("✅ Found 'thumbnail' references in page")
        
    except Exception as e:
        print(f"❌ Error fetching YouTube data: {e}")

def suggest_solutions():
    """Suggest possible solutions based on available tools"""
    
    print(f"\n=== Suggested Solutions ===\n")
    
    available = check_available_tools()
    
    if 'ffmpeg' in available:
        print("🎯 SOLUTION 1: ffmpeg + yt-dlp")
        print("   - Install yt-dlp: pip install yt-dlp")
        print("   - Use yt-dlp to get video stream URL")
        print("   - Use ffmpeg to extract frames at specific timestamps")
        print("   - Most accurate method")
        print()
    
    print("🎯 SOLUTION 2: YouTube Storyboard API")
    print("   - Find YouTube's storyboard images (if available)")
    print("   - Extract specific frames from storyboard grid")
    print("   - Less accurate but doesn't require external tools")
    print()
    
    print("🎯 SOLUTION 3: Improved Static Thumbnails")
    print("   - Use chapter titles/descriptions to select better thumbnails")
    print("   - Create placeholder frames with text")
    print("   - Not ideal but works as fallback")
    print()
    
    print("🎯 SOLUTION 4: Manual Thumbnail Upload")
    print("   - Allow manual upload of chapter thumbnails")
    print("   - Most accurate but requires manual work")

if __name__ == '__main__':
    available = check_available_tools()
    test_youtube_storyboard_api()
    investigate_youtube_data()
    suggest_solutions()