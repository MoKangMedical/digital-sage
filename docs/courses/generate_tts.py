#!/usr/bin/env python3
"""
Generate TTS audio for all 100 Digital Sage sages.
Reads summaries.json and generates .ogg files for each sage.
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path

def main():
    # Read summaries.json
    summaries_path = '/root/digital-sage/docs/courses/summaries.json'
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries = json.load(f)
    
    # Create audio directory if it doesn't exist
    audio_dir = Path('/root/digital-sage/docs/courses/audio')
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    # Track results
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    # Process each sage
    total = len(summaries)
    print(f"Found {total} sages in summaries.json")
    print("=" * 60)
    
    for idx, (cid, sage_data) in enumerate(summaries.items(), 1):
        output_path = str(audio_dir / f"{cid}.ogg")
        
        # Check if file already exists
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"[{idx}/{total}] SKIP {cid} - file already exists")
            skip_count += 1
            continue
        
        text = sage_data.get('text', '')
        name = sage_data.get('name', cid)
        
        print(f"[{idx}/{total}] Generating: {name} ({cid})...")
        
        # Write text to temp file
        temp_text_file = audio_dir / f"{cid}.txt"
        with open(temp_text_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Use edge-tts to generate MP3 first, then convert to OGG
        mp3_path = str(audio_dir / f"{cid}.mp3")
        
        # Choose voice based on language (Chinese vs English)
        # Using zh-CN-XiaoxiaoNeural for Chinese content
        voice = "zh-CN-XiaoxiaoNeural"
        
        try:
            # Generate MP3 with edge-tts
            result = subprocess.run(
                ['edge-tts', '--voice', voice, '--text', text, '--write-media', mp3_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"  ❌ edge-tts failed: {result.stderr[:200]}")
                fail_count += 1
                continue
            
            if not os.path.exists(mp3_path) or os.path.getsize(mp3_path) == 0:
                print(f"  ❌ MP3 file not created")
                fail_count += 1
                continue
            
            # Convert MP3 to OGG Opus using ffmpeg
            ffmpeg_result = subprocess.run(
                ['ffmpeg', '-i', mp3_path, '-acodec', 'libopus', '-ac', '1', '-b:a', '64k', '-vbr', 'off', output_path, '-y'],
                capture_output=True,
                timeout=30
            )
            
            if ffmpeg_result.returncode != 0:
                print(f"  ❌ ffmpeg conversion failed")
                fail_count += 1
                continue
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                file_size = os.path.getsize(output_path)
                print(f"  ✅ Success: {output_path} ({file_size:,} bytes)")
                success_count += 1
                # Clean up MP3
                os.remove(mp3_path)
            else:
                print(f"  ❌ OGG file not created")
                fail_count += 1
                
        except subprocess.TimeoutExpired:
            print(f"  ❌ Timeout")
            fail_count += 1
        except Exception as e:
            print(f"  ❌ Exception: {type(e).__name__}: {e}")
            fail_count += 1
        finally:
            # Clean up temp text file
            if temp_text_file.exists():
                temp_text_file.unlink()
        
        # Small delay to avoid rate limiting
        time.sleep(0.2)
    
    # Summary
    print("=" * 60)
    print(f"COMPLETE: {success_count} generated, {skip_count} skipped, {fail_count} failed")
    print(f"Total sages: {total}")
    
    # List generated files
    audio_files = sorted(audio_dir.glob('*.ogg'))
    print(f"Audio files in directory: {len(audio_files)}")
    for f in audio_files:
        print(f"  - {f.name} ({f.stat().st_size:,} bytes)")

if __name__ == '__main__':
    main()
