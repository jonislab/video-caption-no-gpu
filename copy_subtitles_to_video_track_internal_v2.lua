--[[
DaVinci Resolve Internal Script (Lua): Copy Subtitle Track Clips to a Video Track (v2)
======================================================================================
Designed to run INTERNALLY inside DaVinci Resolve (Free or Studio 21.1+) via:
  - Workspace > Scripts > Utility
  - Workspace > Console (Lua)

Lua 5.1 / LuaJIT translation of copy_subtitles_to_video_track_internal_v2.py:
- Uses the built-in `resolve` global (with `bmd.scriptapp("Resolve")` fallback).
- Supports both track numbers (e.g. 1) and track names (e.g. "Subtitle 1") for `SUBTITLE_TRACK`.
- Defaults to `TARGET_VIDEO_TRACK = 2` and `SUBTITLE_TRACK = "Subtitle 1"`
  (set `TARGET_VIDEO_TRACK = nil` to auto-add a new track).
]]

-- =============================================================================
-- USER CONFIGURATION
-- =============================================================================
local TEMPLATE_NAME = "TFx-Caption"   -- Title template name in Media Pool
local SUBTITLE_TRACK = "Subtitle 1"    -- Subtitle track index (e.g. 1) or track name (e.g. "Subtitle 1")
local TARGET_VIDEO_TRACK = 2           -- Target video track index (e.g. 2), or nil to auto-add a new track
-- =============================================================================


local function trim(s)
    if type(s) ~= "string" then
        return ""
    end
    return s:match("^%s*(.-)%s*$")
end


local function strip_extension(filename)
    if type(filename) ~= "string" then
        return ""
    end
    return filename:match("^(.+)%.[^%.]+$") or filename
end


local function get_resolve_object()
    if resolve ~= nil then
        return resolve
    end

    if bmd ~= nil and bmd.scriptapp ~= nil then
        local res = bmd.scriptapp("Resolve")
        if res ~= nil then
            return res
        end
    end

    if Resolve ~= nil then
        local ok, res = pcall(Resolve)
        if ok and res ~= nil then
            return res
        end
    end

    return nil
end


local function find_clip_recursive(folder, target_name)
    if not folder then
        return nil
    end

    local target_lower = string.lower(trim(target_name))
    local clips = folder:GetClipList() or {}
    for _, clip in ipairs(clips) do
        local clip_name = clip:GetName() or ""
        local name_no_ext = strip_extension(clip_name)
        if string.lower(trim(clip_name)) == target_lower or string.lower(trim(name_no_ext)) == target_lower then
            return clip
        end
    end

    local subfolders = folder:GetSubFolderList() or {}
    for _, subfolder in ipairs(subfolders) do
        local found = find_clip_recursive(subfolder, target_name)
        if found then
            return found
        end
    end

    return nil
end


local function find_text_tool_in_comp(comp)
    if not comp then
        return nil
    end

    local candidates = { "Template", "TextPlus1", "TextPlus" }
    for _, candidate in ipairs(candidates) do
        local tool = comp:FindTool(candidate)
        if tool then
            return tool
        end
    end

    local tool_list = comp:GetToolList() or {}
    for _, tool in pairs(tool_list) do
        local attrs = tool:GetAttrs() or {}
        local reg_id = attrs.TOOLS_RegID
        if reg_id == "TextPlus" or reg_id == "Template" or reg_id == "MultiText" then
            return tool
        end
    end

    return nil
end


local function resolve_subtitle_track_index(timeline, subtitle_track)
    local track_count = timeline:GetTrackCount("subtitle") or 0
    if track_count < 1 then
        return nil, 0
    end

    if type(subtitle_track) == "number" then
        local idx = math.floor(subtitle_track)
        if idx >= 1 and idx <= track_count then
            return idx, track_count
        end
        return nil, track_count
    end

    if type(subtitle_track) == "string" then
        local cleaned = trim(subtitle_track)
        if cleaned:match("^%d+$") then
            local idx = tonumber(cleaned)
            if idx and idx >= 1 and idx <= track_count then
                return idx, track_count
            end
            return nil, track_count
        end

        local cleaned_lower = string.lower(cleaned)
        for idx = 1, track_count do
            local track_name = timeline:GetTrackName("subtitle", idx) or ""
            if string.lower(trim(track_name)) == cleaned_lower then
                return idx, track_count
            end
        end

        local trailing_num = cleaned:match("(%d+)$")
        if trailing_num then
            local idx = tonumber(trailing_num)
            if idx and idx >= 1 and idx <= track_count then
                return idx, track_count
            end
        end
    end

    return nil, track_count
end


local function copy_subtitles_to_video_track(template_name, subtitle_track, target_video_track)
    print("==================================================")
    print("  COPY SUBTITLES TO VIDEO TRACK (INTERNAL LUA v2) ")
    print("==================================================")

    -- 1. Acquire Resolve API objects
    local resolve_obj = get_resolve_object()
    if not resolve_obj then
        print("Error: Could not access the DaVinci Resolve scripting API.")
        print("Tip: Run this script from Workspace > Scripts > Utility or Workspace > Console (Lua).")
        return false
    end

    local project_manager = resolve_obj:GetProjectManager()
    if not project_manager then
        print("Error: Failed to access Project Manager.")
        return false
    end

    local project = project_manager:GetCurrentProject()
    if not project then
        print("Error: No project is currently open.")
        return false
    end

    local timeline = project:GetCurrentTimeline()
    if not timeline then
        print("Error: No active timeline found in the current project.")
        return false
    end

    local media_pool = project:GetMediaPool()
    if not media_pool then
        print("Error: Failed to access Media Pool.")
        return false
    end

    local root_folder = media_pool:GetRootFolder()

    print("Project        : " .. tostring(project:GetName()))
    print("Timeline       : " .. tostring(timeline:GetName()))
    print("Template Name  : " .. tostring(template_name))

    -- 2. Locate template clip in Media Pool (searches Master + all nested bins)
    local template_clip = find_clip_recursive(root_folder, template_name)
    if not template_clip then
        print("Error: Template '" .. tostring(template_name) .. "' was not found anywhere in the Media Pool.")
        print("Make sure the template clip is inside your project's Media Pool.")
        return false
    end

    print("Template Clip  : " .. tostring(template_clip:GetName()))

    -- 3. Resolve and read subtitle items from the subtitle track
    local sub_track_idx, subtitle_track_count = resolve_subtitle_track_index(timeline, subtitle_track)
    if subtitle_track_count < 1 then
        print("Error: This timeline has no subtitle tracks.")
        return false
    end

    if not sub_track_idx then
        print(string.format(
            "Error: Could not find Subtitle Track '%s' (available subtitle tracks: %d).",
            tostring(subtitle_track),
            subtitle_track_count
        ))
        return false
    end

    local sub_items = timeline:GetItemListInTrack("subtitle", sub_track_idx) or {}
    if #sub_items == 0 then
        print(string.format(
            "No subtitle clips found on Subtitle Track %d ('%s').",
            sub_track_idx,
            tostring(subtitle_track)
        ))
        return false
    end

    print(string.format(
        "Subtitle Clips : Found %d item(s) on Subtitle Track %d",
        #sub_items,
        sub_track_idx
    ))

    -- 4. Prepare target video track
    local current_video_tracks = timeline:GetTrackCount("video") or 1
    local dest_track
    if target_video_track == nil then
        if not timeline:AddTrack("video") then
            print("Error: Could not add a new video track to the timeline.")
            return false
        end
        dest_track = timeline:GetTrackCount("video")
        print(string.format("Target Track   : Created new Video Track %d", dest_track))
    else
        dest_track = math.floor(tonumber(target_video_track))
        if dest_track < 1 then
            print("Error: TARGET_VIDEO_TRACK must be >= 1.")
            return false
        end
        while (timeline:GetTrackCount("video") or 0) < dest_track do
            if not timeline:AddTrack("video") then
                print(string.format("Error: Failed while adding Video Track up to %d.", dest_track))
                return false
            end
        end
        print(string.format(
            "Target Track   : Video Track %d (existing tracks: %d)",
            dest_track,
            current_video_tracks
        ))
    end

    -- 5. Copy each subtitle clip to the target video track using TFx-Caption2
    local copied_count = 0
    local text_updated_count = 0

    for idx, sub_item in ipairs(sub_items) do
        local subtitle_text = sub_item:GetName() or ""
        local start_frame = sub_item:GetStart()
        local duration_frames = sub_item:GetDuration()

        if not duration_frames or duration_frames <= 0 then
            print(string.format(
                "  [%03d] Skipping subtitle with non-positive duration (%s).",
                idx,
                tostring(duration_frames)
            ))
        else
            local clip_info = {
                mediaPoolItem = template_clip,
                startFrame = 0,
                endFrame = duration_frames,
                recordFrame = start_frame,
                trackIndex = dest_track,
                mediaType = 1,
            }

            local append_result = media_pool:AppendToTimeline({ clip_info })
            if not append_result or #append_result == 0 then
                print(string.format(
                    "  [%03d] Warning: Failed to append clip at frame %s.",
                    idx,
                    tostring(start_frame)
                ))
            else
                copied_count = copied_count + 1
                local new_item = append_result[1]

                if (new_item:GetFusionCompCount() or 0) > 0 then
                    local comp = new_item:GetFusionCompByIndex(1)
                    local text_tool = find_text_tool_in_comp(comp)
                    if text_tool then
                        text_tool:SetInput("StyledText", subtitle_text)
                        text_updated_count = text_updated_count + 1
                    else
                        print(string.format(
                            "  [%03d] Warning: No TextPlus/Template node found in '%s' comp.",
                            idx,
                            tostring(template_name)
                        ))
                    end
                else
                    print(string.format(
                        "  [%03d] Warning: Appended '%s' clip has no Fusion comp.",
                        idx,
                        tostring(template_name)
                    ))
                end
            end
        end
    end

    print("--------------------------------------------------")
    print(string.format(
        "Copied Clips   : %d/%d added to Video Track %d",
        copied_count,
        #sub_items,
        dest_track
    ))
    print(string.format(
        "Text Updated   : %d/%d Fusion titles updated",
        text_updated_count,
        copied_count
    ))
    print("==================================================")
    return copied_count > 0
end


local function main()
    copy_subtitles_to_video_track(
        TEMPLATE_NAME,
        SUBTITLE_TRACK,
        TARGET_VIDEO_TRACK
    )
end


local ok, err = xpcall(main, function(e)
    if debug and debug.traceback then
        return debug.traceback(e, 2)
    end
    return tostring(e)
end)

if not ok then
    print("Critical error during execution: " .. tostring(err))
end
