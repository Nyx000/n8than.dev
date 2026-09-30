-- OBS script for the /live stream: two hotkeys that flip the webcam overlay and the mic.
-- Loaded by the local OBS scene collection (Tools > Scripts); nothing on the server uses it.
-- Works across every scene (one per game, each with its own theme): the shared "Webcam" source
-- and any item named "Webcam Frame ..." flip together, so all scenes stay in step and the
-- automatic scene switcher never lands on a scene in the other state. "Mic" is one shared
-- audio source. The webcam starts off, the mic live.
-- Default binds are Ctrl+Alt+W and Ctrl+Alt+M; rebinding in OBS Settings > Hotkeys persists.
obs = obslua

local hotkeys = {}

local function is_webcam_item(name)
  return name == "Webcam" or name:sub(1, #"Webcam Frame") == "Webcam Frame"
end

-- Set the visibility of every webcam item in every scene.
local function set_webcam_visible(visible)
  local scenes = obs.obs_frontend_get_scenes()
  if scenes == nil then return end
  for _, src in ipairs(scenes) do
    local items = obs.obs_scene_enum_items(obs.obs_scene_from_source(src))
    if items ~= nil then
      for _, item in ipairs(items) do
        if is_webcam_item(obs.obs_source_get_name(obs.obs_sceneitem_get_source(item))) then
          obs.obs_sceneitem_set_visible(item, visible)
        end
      end
      obs.sceneitem_list_release(items)
    end
  end
  obs.source_list_release(scenes)
end

-- The scene on air decides the direction; every scene then follows it.
local function toggle_webcam()
  local src = obs.obs_frontend_get_current_scene()
  if src == nil then return end
  local item = obs.obs_scene_find_source(obs.obs_scene_from_source(src), "Webcam")
  local show = item ~= nil and not obs.obs_sceneitem_visible(item)
  obs.obs_source_release(src)
  set_webcam_visible(show)
end

local function toggle_mic()
  local src = obs.obs_get_source_by_name("Mic")
  if src == nil then return end
  obs.obs_source_set_muted(src, not obs.obs_source_muted(src))
  obs.obs_source_release(src)
end

local TOGGLES = {
  { key = "webcam", label = "Toggle webcam (live)", fn = toggle_webcam,
    default = '{"key":"OBS_KEY_W","control":true,"alt":true,"shift":false,"command":false}' },
  { key = "mic", label = "Toggle mic (live)", fn = toggle_mic,
    default = '{"key":"OBS_KEY_M","control":true,"alt":true,"shift":false,"command":false}' },
}

function script_description()
  return "Hotkeys for the /live stream: toggle the webcam overlay and the mic."
end

function script_load(settings)
  for _, t in ipairs(TOGGLES) do
    local id = obs.obs_hotkey_register_frontend("live_toggle_" .. t.key, t.label, function(pressed)
      if pressed then t.fn() end
    end)
    local arr = obs.obs_data_get_array(settings, "hotkey_" .. t.key)
    if obs.obs_data_array_count(arr) == 0 then
      obs.obs_data_array_release(arr)
      arr = obs.obs_data_array_create()
      local combo = obs.obs_data_create_from_json(t.default)
      obs.obs_data_array_push_back(arr, combo)
      obs.obs_data_release(combo)
    end
    obs.obs_hotkey_load(id, arr)
    obs.obs_data_array_release(arr)
    hotkeys[t.key] = id
  end
end

function script_save(settings)
  for key, id in pairs(hotkeys) do
    local arr = obs.obs_hotkey_save(id)
    obs.obs_data_set_array(settings, "hotkey_" .. key, arr)
    obs.obs_data_array_release(arr)
  end
end
