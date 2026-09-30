-- OBS script for the /live stream: two hotkeys that flip the webcam overlay and the mic.
-- Loaded by the local OBS scene collection (Tools > Scripts); nothing on the server uses it.
-- Expects scene "Live" with items "Webcam" + "Webcam Frame" (the overlay/ chrome around it),
-- "Mic Badge", and an audio source "Mic". Everything starts off.
-- Default binds are Ctrl+Alt+W and Ctrl+Alt+M; rebinding in OBS Settings > Hotkeys persists.
obs = obslua

local hotkeys = {}

-- Set the visibility of the named items in scene "Live"; missing items are skipped.
local function set_visible(names, visible)
  local src = obs.obs_get_source_by_name("Live")
  if src == nil then return end
  local scene = obs.obs_scene_from_source(src)
  for _, name in ipairs(names) do
    local item = obs.obs_scene_find_source(scene, name)
    if item ~= nil then obs.obs_sceneitem_set_visible(item, visible) end
  end
  obs.obs_source_release(src)
end

local function toggle_webcam()
  local src = obs.obs_get_source_by_name("Live")
  if src == nil then return end
  local item = obs.obs_scene_find_source(obs.obs_scene_from_source(src), "Webcam")
  local show = item ~= nil and not obs.obs_sceneitem_visible(item)
  obs.obs_source_release(src)
  set_visible({ "Webcam", "Webcam Frame" }, show)
end

-- The badge follows the mic, so viewers (and the streamer, in the preview) see when it is live.
local function toggle_mic()
  local src = obs.obs_get_source_by_name("Mic")
  if src == nil then return end
  local live = obs.obs_source_muted(src)
  obs.obs_source_set_muted(src, not live)
  obs.obs_source_release(src)
  set_visible({ "Mic Badge" }, live)
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
