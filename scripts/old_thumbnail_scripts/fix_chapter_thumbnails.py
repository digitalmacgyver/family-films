#!/usr/bin/env python3
"""
Fix chapter thumbnails by re-extracting only Start column images
"""
import subprocess
from pathlib import Path

def fix_thumbnails():
    """Re-extract thumbnails with correct Start column filtering"""
    
    # Files that were processed and need to be corrected
    files_to_fix = [
        "57-PT_FROS - Josephine Southwest Trip Grand Canyon Bryce Canyon Zion Calico Ghost Town.xls",
        "58-V1_FROS - Road Trip Utah Nevada Wyoming Michigan.xls", 
        "58-V2_FROS - Canada Road Trip Montana Victoria BC.xls",
        "59-HI_FROS - Hawaii Trip.xls",
        "HR-1-4_FROS - Multiple Reels Mostly Haywards Myres and Wrens Victoria BC Knotts Berry Farm Tubing Christmas Rose Parade Santas Village.xls",
        "L-55C_FROS - Bob Lindner Film 4 - Train and Lindners with Earl and Rosabell.xls",
    ]
    
    print("FIXING CHAPTER THUMBNAILS")
    print("=" * 50)
    print("Re-extracting thumbnails using only Start column images")
    print()
    
    success_count = 0
    
    for excel_file in files_to_fix:
        try:
            print(f"Fixing: {excel_file}")
            
            # Run import command to re-assign thumbnails correctly
            result = subprocess.run([
                "python", "manage.py", "import_chapter_metadata", 
                "--file", excel_file
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Count thumbnail assignments from output
                output_lines = result.stdout.split('\n')
                extraction_line = [line for line in output_lines if "using" in line and "from Start column" in line]
                assigned_lines = [line for line in output_lines if "Assigned thumbnail:" in line]
                
                if extraction_line:
                    print(f"  ✅ {extraction_line[0].strip()}")
                    print(f"  ✅ {len(assigned_lines)} thumbnails assigned")
                    success_count += 1
                else:
                    print(f"  ⚠️  Processed but no extraction info found")
            else:
                print(f"  ❌ Failed: {result.stderr}")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
        
        print()
    
    print("=" * 50)
    print(f"SUMMARY: {success_count}/{len(files_to_fix)} files corrected")
    print()
    print("✨ Chapter thumbnails now use only Start column images!")
    print("   View at: http://127.0.0.1:8000/films/")

if __name__ == "__main__":
    fix_thumbnails()