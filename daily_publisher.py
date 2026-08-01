import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Gal Gadot's Most Iconic Wonder Woman Moments",
        "Why Gal Gadot Is Hollywood's Wonder Woman",
        "Gal Gadot — The Woman Behind the Lasso",
        "Best Gal Gadot Movie Scenes of All Time",
        "Gal Gadot's Journey From Miss Israel to Wonder Woman",
        "Top 5 Gal Gadot Performances You Must Watch",
        "Wonder Woman: The Legacy of Gal Gadot",
        "Gal Gadot Style and Grace on the Red Carpet",
        "The Power and Grace of Gal Gadot",
        "Gal Gadot Moments That Made Us Fall in Love",
        "Behind the Scenes With Gal Gadot",
        "Gal Gadot's Inspiring Words on Strength",
        "Wonder Woman Through the Years",
        "Gal Gadot — Beauty, Brains and Bravery",
        "Rediscovering Gal Gadot's Greatest Roles",
    ]

    fallback_descriptions = [
        "From the battlefields of Themyscira to the screens of the world, Gal Gadot redefined what a superhero looks like. Her Wonder Woman isn't just powerful — she's compassionate, fierce, and endlessly inspiring. This is a tribute to the woman who taught us that love and strength can coexist. Drop a 💪 if you love Gal Gadot! #galgadot #wonderwoman #dccomics #movieclips #actress #hollywood #wonderwoman1984 #fanpage #gadot #superhero",
        "Gal Gadot didn't just play Wonder Woman — she became a symbol of empowerment. From her roots as Miss Israel and an IDF soldier to becoming one of Hollywood's most beloved action stars, her journey is proof that strength comes in many forms. Here's a look at the moments that defined her career. Like if you admire her! ✨ #galgadot #wonderwoman #inspiration #hollywood #actress #journey #empowerment #superhero #dccomics #fanpage",
        "There's a reason Gal Gadot is called a real-life Wonder Woman. Beyond the lasso and the shield, she brings warmth, humor, and genuine heart to every role. These are the scenes that show off her incredible range — from action to emotion. Comment your favorite Gal Gadot movie below! 🎬 #galgadot #wonderwoman #movies #actress #bestscenes #cinema #hollywood #fanpage #dccomics #filmlover",
        "The story of Gal Gadot is one of defying expectations. A beauty queen turned action star, she proved that women can lead blockbuster franchises and inspire generations. This tribute celebrates her rise, her roles, and her impact on Hollywood. Share this with a fellow Wonder Woman fan! 🌟 #galgadot #wonderwoman #hollywood #inspiration #actress #empowerment #womeninstem #film #dccomics #fanpage",
        "Wonder Woman's true superpower was always her heart. Gal Gadot brought that heart to the screen, making Diana Prince a hero for the ages. From the iconic no-man's-land scene to her quiet moments of compassion, she gave us a hero to believe in. Double tap if Gal Gadot is your favorite hero! 💛 #galgadot #wonderwoman #diana prince #superhero #dccomics #movieclips #hero #inspiration #fanpage #cinema",
        "Gal Gadot's red-carpet style is as legendary as her action scenes. Elegant, confident, and effortlessly graceful, she redefines glamour every time she steps out. These fashion moments show the woman behind the warrior. Which look is your favorite? Comment below! 👗 #galgadot #redcarpet #fashion #style #glamour #hollywood #elegance #actress #wonderwoman #fanpage",
        "Strength. Grace. Compassion. These are the qualities Gal Gadot embodies both on and off screen. Her journey from Israel to the global stage is an inspiration to everyone chasing their dreams. This tribute is for every fan who sees a little Wonder Woman in themselves. Drop a 👑 if you're inspired! #galgadot #wonderwoman #inspiration #strength #grace #journey #empowerment #hollywood #actress #fanpage",
        "Few actors become icons. Gal Gadot did it by bringing authenticity to every role — whether she's saving the world as Wonder Woman or delivering a heartfelt performance in a drama. Her filmography is a masterclass in versatility. Save this for your next movie night! 🍿 #galgadot #movies #actress #filmography #wonderwoman #hollywood #cinema #mustwatch #dccomics #fanpage",
        "Behind every legendary character is a legendary person. Gal Gadot's warmth, humor, and humility shine through in every interview and behind-the-scenes moment. Here's a look at the real woman behind Wonder Woman. Like if you love seeing actors being their authentic selves! 🎥 #galgadot #behindthescenes #wonderwoman #authentic #interview #hollywood #actress #reel #fanpage #bts",
        "Gal Gadot's words are as powerful as her on-screen action. Her quotes on strength, self-belief, and kindness resonate with millions. Here are the moments where she reminded us all to be brave and stay true to ourselves. Share this with someone who needs the reminder! 💬 #galgadot #quotes #inspiration #wonderwoman #strength #motivation #selfbelief #hollywood #actress #fanpage",
        "From the big screen to our hearts, Gal Gadot has captured the imagination of audiences worldwide. This fan page tribute celebrates the actress, the icon, and the woman who inspires millions every day. We're just a fanpage — no impersonation, just appreciation. Drop a ❤️ if you're a Gadot fan! #galgadot #wonderwoman #fanpage #tribute #hollywood #actress #dccomics #love #appreciation #gadot",
        "What makes a hero? Gal Gadot would tell you it's courage, compassion, and the willingness to stand up for what's right. Her portrayal of Wonder Woman gave the world a hero rooted in love and justice. Here's to the moments that defined her legacy. Comment your favorite Wonder Woman scene! 🌟 #galgadot #wonderwoman #hero #legacy #dccomics #movieclips #courage #justice #hollywood #fanpage",
        "There's an undeniable magic in watching Gal Gadot on screen. Whether it's the epic action of Wonder Woman or the charm of her lighter roles, she commands every frame. This is a celebration of her artistry and the joy she brings to audiences. Double tap for Gal Gadot! ✨ #galgadot #wonderwoman #cinema #acting #talent #hollywood #movieclips #artistry #dccomics #fanpage",
        "One woman. One lasso. A billion hearts. Gal Gadot's Wonder Woman became a cultural phenomenon, inspiring fans of all ages around the globe. From her iconic entrance to the battles that defined her, these are the moments we'll never forget. Share this with a fellow fan! 🦸‍♀️ #galgadot #wonderwoman #iconic #culturalphenomenon #dccomics #movieclips #nostalgia #superhero #hollywood #fanpage",
        "Gal Gadot proves that you can be strong, kind, and glamorous all at once. Her impact on cinema and culture goes far beyond the screen — she's a role model for courage and grace. This fan tribute is our little way of celebrating her. Like if Gal Gadot inspires you! 💖 #galgadot #wonderwoman #rolemodel #inspiration #hollywood #actress #grace #strength #fanpage #tribute",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "admiring and celebratory — speak as a devoted fan paying tribute",
        "epic and cinematic — make viewers feel the wonder of her hero moments",
        "warm and appreciative — celebrate her talent, grace and character",
        "inspiring and uplifting — highlight her strength and journey",
        "fun and nostalgic — celebrate iconic movie moments fans love",
        "respectful and heartfelt — appreciate the person behind the character",
        "energetic and exciting — build hype around her best scenes",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'WonderTok Lens'. "
        f"It is a fan page dedicated to the Hollywood actress Gal Gadot, best known as Wonder Woman. "
        f"It shares appreciation content, iconic movie moments, and tributes to her career. "
        f"It is an unofficial fan page that does not impersonate anyone - just celebrates her work. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"Like if you love Gal Gadot! Comment your favorite Gal Gadot movie below! Share this with a fellow Wonder Woman fan! Follow WonderTok Lens for daily Gal Gadot appreciation! "
        f"Include relevant hashtags in ALL LOWERCASE such as #galgadot #wonderwoman #dccomics #hollywood #actress #movieclips #superhero #dianaprice #gadot #fanpage #cinema #movie #wonderwoman1984 #appreciation. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["galgadot", "wonderwoman", "dccomics", "hollywood", "actress", "movieclips", "superhero", "dianaprice", "gadot", "fanpage", "cinema", "movie", "wonderwoman1984", "appreciation"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
