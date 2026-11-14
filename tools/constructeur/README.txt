HSFA builder -- from your discs to the HSFA games, nothing to install
====================================================================

You need:
  - your PS2 image of Street Fighter Alpha Anthology (USA, SLUS-21317), .iso or .chd;
  - (optional) your PSP ISO of Street Fighter Alpha 3 MAX (Europe, ULES-00235), .iso or .chd:
    it adds Upper MAX (Eagle, Maki, Yun, Ingrid);
  - about 3 GB of free space (5 GB from a .chd) and 10 to 20 minutes.
The builder contains no game data: everything is read from YOUR images.

1. Download
   From the project release, take the zip for your system:
     Windows: hsfa-constructeur-windows-x86_64.zip
     macOS:   hsfa-constructeur-macos-arm64.zip (Apple M1 and later) or macos-x86_64 (Intel)
     Linux:   hsfa-constructeur-linux-x86_64.zip (PC) or linux-aarch64 (64-bit ARM)
   Unzip it anywhere. Checksums: SHA256SUMS-constructeur.txt in the release.

2. Run
   Windows: double-click hsfa-constructeur.exe, or drop the PS2 image onto it.
   macOS / Linux: double-click, or in a terminal:
       ./hsfa-constructeur                                  (window)
       ./hsfa-constructeur Anthology.iso --psp MAX.iso      (no window)
   In the window: pick the PS2 image, the PSP ISO if you have it, the output folder, then "Build".
   The builder first announces the estimated time (per game and in total), then the bar shows the current step
   (step n / N) and the time left.

3. Warnings (expected: the executable is not signed)
   Windows: "Windows protected your PC" (SmartScreen) -> "More info" -> "Run anyway". Some antivirus tools are wary
     of this kind of executable (PyInstaller): check the SHA-256 checksum if in doubt.
   macOS: "cannot be opened ... unidentified developer" -> System Settings > Privacy & Security > "Open Anyway".
     Or in a terminal: xattr -d com.apple.quarantine hsfa-constructeur
   Linux: if double-clicking does nothing: chmod +x hsfa-constructeur

4. Where the zips go
   When it is done (sound, window brought to the front, message "Done: N games in ..."), the output folder
   (HSFA-sortie next to the executable by default) holds the zips themselves:
     sfa3hsfa.zip (SFA3), sfa3uhsfa.zip (Upper), sfa3hhsfa.zip (Hyper), sfa3umhsfa.zip (Upper MAX, with the PSP ISO).
   Copy them WITHOUT RENAMING into RetroArch's (or your console's) ROM folder, next to the project's
   "FinalBurn Neo HSFA" core, then load a zip with that core. Guides: docs/guide/ in the repository.
   The hsfa-travail subfolder (work files) can be deleted; keeping it makes a rebuild faster.
   (An output folder from an earlier version, with archives/, is tidied up this way on the first run.)

Problem? Attach hsfa-travail/journal.txt (output folder) to an issue on the repository, in English or French.
Third-party licences: TIERS.md.
