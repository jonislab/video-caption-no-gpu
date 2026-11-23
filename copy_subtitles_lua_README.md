# DaVinci Resolve Subtitle to Video Track Converter (Lua Edition v2)

`copy_subtitles_to_video_track_internal_v2.lua` is a lightweight, zero-dependency **Lua 5.1 / LuaJIT script** that converts native DaVinci Resolve Subtitle Track clips into customizable **Fusion Text+ title clips** placed directly onto a designated **Video Track**.

This script was created specifically to run **internally inside both DaVinci Resolve Free and Studio (v18, v19, v20, and v21+)** without requiring external Python environments, pip packages, or paid Studio scripting licenses.

---

## 💡 Why Lua in DaVinci Resolve 21.1+?

In **DaVinci Resolve 21.1 and later**, Blackmagic Design moved Python scripting (both external API connections and internal `.py` scripts under `Workspace > Scripts`) to the **Studio Edition**. 

However, **Lua 5.1 / LuaJIT scripting remains fully unlocked and functional in the Free version of DaVinci Resolve**. By writing this automation in native Lua:
- ✅ **Works 100% in DaVinci Resolve Free** (as well as Studio).
- ✅ **Appears in `Workspace > Scripts > Utility`** automatically.
- ✅ **Zero external dependencies**: runs directly inside Resolve's built-in LuaJIT runtime.
- ✅ **No terminal or Python configuration needed**: click and run directly from the UI.

---

## ✨ Features

- **🎯 Exact Frame Synchronization**: Reads each subtitle clip's start frame (`GetStart()`) and duration (`GetDuration()`), placing the corresponding Fusion title card at the exact timeline position.
- **🎨 Custom Fusion Title Templates**: Duplicates your preferred template (default: **`TFx-Caption2`**) with custom animations, drop shadows, fonts, and motion graphics intact.
- **✍️ Automatic Fusion Text Injection**: Automatically inspects the Fusion composition (`TextPlus`, `Template`, or `MultiText` tool) and updates the `StyledText` input with the subtitle's text content.
- **📂 Recursive Media Pool Search**: Scans the root `Master` folder and all nested subfolders/bins to locate your template clip even if organized deep within your bin hierarchy.
- **🔀 Flexible Track Selection**:
  - `SUBTITLE_TRACK`: accepts an integer index (e.g. `1`), a string index (`"1"`), or a track name (e.g. `"Subtitle 1"`).
  - `TARGET_VIDEO_TRACK`: specify an exact video track (e.g. `2`), or set to `nil` to automatically create a new video track at the top of the stack.
- **🛡️ Console-Safe Diagnostics**: Uses standard Lua `print()` and protected execution (`xpcall` with `debug.traceback`), eliminating `fu_stdout.flush` crashes and displaying clear progress in **Workspace > Console**.

---

## 📋 Prerequisites & Setup

1. **DaVinci Resolve (Free or Studio)**: Versions 18.x, 19.x, 20.x, or 21.x+.
2. **Subtitle Track**: An active timeline with subtitle clips on Subtitle Track 1 (or your configured subtitle track name).
3. **Template in Media Pool**: A Fusion title template clip (e.g. **`TFx-Caption2`**) placed anywhere in your project's Media Pool.

---

## 📥 Installation

Place **`copy_subtitles_to_video_track_internal_v2.lua`** into Resolve’s global or user-specific `Scripts/Utility` directory:

### Windows
```text
%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\
```
*(Full path: `C:\Users\<YourUsername>\AppData\Roaming\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Utility\`)*

### macOS
```text
~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility/
```

### Linux
```text
~/.local/share/DaVinciResolve/Fusion/Scripts/Utility/
```

> **Note**: Restart DaVinci Resolve after copying the file so it enumerates the script into the menu.

---

## ⚙️ Configuration

Open `copy_subtitles_to_video_track_internal_v2.lua` in any text editor to adjust settings at the top of the file:

```lua
-- =============================================================================
-- USER CONFIGURATION
-- =============================================================================
local TEMPLATE_NAME = "TFx-Caption"   -- Title template name in Media Pool
local SUBTITLE_TRACK = "Subtitle 1"    -- Track index (e.g. 1) or track name ("Subtitle 1")
local TARGET_VIDEO_TRACK = 2           -- Target video track index (e.g. 2), or nil for auto-new track
-- =============================================================================
```

### Configuration Options

| Variable | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `TEMPLATE_NAME` | `string` | `"TFx-Caption"` | Name of the Fusion Title template clip in your Media Pool. |
| `SUBTITLE_TRACK`| `string` / `number` | `"Subtitle 1"` | Name (e.g. `"Subtitle 1"`) or 1-based index (e.g. `1`) of source subtitle track. |
| `TARGET_VIDEO_TRACK` | `number` / `nil` | `2` | Target video track index (e.g. `2`). Set to `nil` to auto-add a fresh top video track. |

---

## 🚀 How to Run

### Method 1: From the Workspace Menu (Recommended)
1. Open your project in DaVinci Resolve and make sure your timeline is active.
2. Optional: Open **Workspace > Console** to watch live progress logs.
3. Click **Workspace > Scripts > Utility > copy_subtitles_to_video_track_internal_v2**.

### Method 2: From the Console (Lua Prompt)
1. Open **Workspace > Console**.
2. Click the **Lua** button at the top of the console window.
3. Paste and run:
   ```lua
   dofile(fusion:MapPath("Scripts:Utility/copy_subtitles_to_video_track_internal_v2.lua"))
   ```

---

## 🖥️ Console Output Example

```text
==================================================
  COPY SUBTITLES TO VIDEO TRACK (INTERNAL LUA v2) 
==================================================
Project        : Demo_Project
Timeline       : Main_Timeline
Template Name  : TFx-Caption
Template Clip  : TFx-Caption
Subtitle Clips : Found 32 item(s) on Subtitle Track 1
Target Track   : Video Track 2 (existing tracks: 2)
--------------------------------------------------
Copied Clips   : 32/32 added to Video Track 2
Text Updated   : 32/32 Fusion titles updated
==================================================
```

---

## 🛠️ Troubleshooting

- **Script does not appear in `Workspace > Scripts > Utility`**:
  - Make sure the file extension is strictly **`.lua`** (not `.lua.txt`).
  - Confirm the folder path matches your operating system's `Fusion/Scripts/Utility` location.
  - Restart DaVinci Resolve.
- **`Error: Template 'TFx-Caption' was not found anywhere in the Media Pool`**:
  - Ensure you have imported or created your title template in the Media Pool.
  - Check spelling and capitalization of `TEMPLATE_NAME`.
- **`No subtitle clips found on Subtitle Track 1`**:
  - Verify that your subtitle track contains clips and is not muted/disabled.
  - Check if your subtitle track is named differently (e.g. `"Subtitles"` vs `"Subtitle 1"`).
- **Text does not appear on the new video track**:
  - Ensure your title template has a `TextPlus` or `Template` node.
  - Confirm Video Track 2 is visible and not hidden beneath an opaque upper video track.

---

## 📄 License
This script is open-source and free to use under the [MIT License](LICENSE).
