-- MEMOIRE EXTERNE DU BANC (HANDOFF §75) : fichiers charges par le portage a adresse FIXE (ex. frames de
-- sprites, fichier 289 en $A04000), servis au 68K par un tap de lecture sur la plage non projetee.
-- Fichiers : ext_<adresse>.bin (mots gros-boutistes) ecrits par mame_test.py.
local W = os.getenv("BANC_DIR") or "<workspace>/work/mame/"   -- (HANDOFF §108) dossier du module (ro5 : work/mame_ro5/)
local sp = manager.machine.devices[":maincpu"].spaces["program"]
BANC_TAPS = BANC_TAPS or {}
-- (HANDOFF §99) tous les blocs ext_<adresse>.bin presents (fichier 289 en $A04000, blocs des persos MAX en $B00000...,
-- Upper : $D40000... §129)
local bases = {}
for _, nom in ipairs({"a04000", "b00000", "b40000", "b80000", "bc0000", "b04000", "c80000", "d40000", "d80000", "dc0000", "e00000"}) do bases[#bases + 1] = tonumber(nom, 16) end
for _, base in ipairs(bases) do
  local f = io.open(W .. string.format("ext_%06x.bin", base), "rb")
  if f then
    local s = f:read("a"); f:close()
    local n = #s
    table.insert(BANC_TAPS, sp:install_read_tap(base, base + n - 1, "ext" .. base, function(offset, data, mask)
      local i = (offset & ~1) - base + 1
      return (s:byte(i) << 8) | s:byte(i + 1)
    end))
  end
end
-- (HANDOFF §121, agent_ro9) blocs externes supplementaires listes dans BANC_DIR/ext_liste.txt (ecrit par mame_test.py)
-- pour les bases absentes de la liste fixe ci-dessus (Hyper : $940000 = fin des donnees, $C84000 = fichier 547)
do
  local connus = {}
  for _, b in ipairs(bases) do connus[string.format("%06x", b)] = true end
  local lst = io.open(W .. "ext_liste.txt", "r")
  if lst then
    for nom in lst:lines() do
      if nom ~= "" and not connus[nom] then
        local base = tonumber(nom, 16)
        local f = io.open(W .. "ext_" .. nom .. ".bin", "rb")
        if f then
          local s = f:read("a"); f:close()
          table.insert(BANC_TAPS, sp:install_read_tap(base, base + #s - 1, "extl" .. nom, function(offset, data, mask)
            local i = (offset & ~1) - base + 1
            return (s:byte(i) << 8) | s:byte(i + 1)
          end))
        end
      end
    end
    lst:close()
  end
end
