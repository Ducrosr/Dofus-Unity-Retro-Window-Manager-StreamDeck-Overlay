<h1 align="center">Dofus Window Manager</h1>

<p align="center"><strong>Dofus Unity &amp; Retro multi-account window manager — with or without Stream Deck</strong></p>

<p align="center">
  Switch characters with <strong>global keyboard shortcuts</strong>, keep your team visible in an <strong>overlay</strong>, and add the <strong>Stream Deck</strong> plugin only if you want it.
</p>

<p align="center">
  <a href="https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/releases/tag/v2.20.0-beta.3"><strong>⬇ Download for Windows</strong></a>
  ·
  <a href="docs/INSTALLATION.md">Installation guide</a>
  ·
  <a href="docs/UTILISATION.md">User guide</a>
</p>

<p align="center">
  <img src=".github/social-preview.png" alt="Dofus Window Manager — Unity and Retro multi-account management with shortcuts, overlay and optional Stream Deck" width="100%">
</p>

[Français](README.md) · **English** · [Español](README.es.md)

> [!NOTE]
> This translation was generated with AI assistance and may contain errors. Corrections are welcome through Issues or Pull Requests on the official repository.

A local Windows window manager for **Dofus Unity** and **Dofus Retro**, designed to make multi-account play easier to read and faster to control. It detects open Dofus windows, keeps their order and switches between them through the **F5/F6 keyboard shortcuts**, the overlay or compact mode. **A Stream Deck is not required**: the bundled plugin is an optional integration for users who own the hardware.

> [!WARNING]
> **This repository is the only official source:**
> <https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay>
>
> Never download Dofus Window Manager from a third-party website, private message or mirror. A modified copy could attempt to steal Ankama credentials, session tokens or personal data. The official application never asks for your Ankama password, two-factor authentication code or account access.
>
> Also read Ankama’s official guidance: **[Recognizing and protecting yourself from phishing](https://support.ankama.com/hc/en-us/articles/201376953-Recognizing-and-Protecting-Yourself-from-Phishing)**.

Version 2.20.0 is the current public beta. It brings together the multilingual interface, overlays, attention requests, portraits, official icons and Unity/Retro themes. The matching Windows executable is available from the [official v2.20.0-beta.3 Release](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/releases/tag/v2.20.0-beta.3).

## Main features

- native Dofus Unity and Retro window detection;
- next/previous character global shortcuts plus eight optional direct shortcuts for positions 1 to 8;
- ordering by buttons or drag and drop;
- per-character alias, custom or bundled class portrait, 39 official stat icons and 20 official profession icons;
- ignored windows remain bound to their Stream Deck keys but leave automatic rotation;
- per-server JSON profiles containing independent order, aliases, portraits and icons, plus complete configuration backups;
- atomic settings and profile writes, with an automatic backup of the last valid settings;
- instant Unity/Retro switching with separate display preferences for each version;
- compact always-on-top mode;
- automatic compact-window and overlay recovery after a monitor-layout change;
- customizable switch notification with content-based automatic width, position, duration and opacity;
- transparent, movable and resizable vertical or horizontal rotation overlay with optional automatic width;
- portraits and icons can be shown or hidden independently in the notification, overlay and Stream Deck;
- orange `!` attention request indicator with optional subtle blinking in the app, overlay and Stream Deck;
- chronological `!1`, `!2`… queue with a **Next alert** action in the app, overlay, F8 shortcut and Stream Deck;
- twelve themes available in both game modes: Standard, Bonta, Brakmar, Tribute, Gold and Steel, Belladone, Unicorn, Emerald Mine, Sufokia, Pandala, Wabbit and Retro;
- French by default, plus English and Spanish selected with graphical flag buttons;
- settings organized into General, Appearance and Shortcuts tabs;
- a mandatory first-launch security warning shown before global shortcuts are enabled;
- separate display reset that preserves profiles and character customization;
- optional official-release update check with no automatic download.

Standard is the default theme for both Unity and Retro. Every theme can be selected in either mode, and the application remembers one theme and a separate set of display preferences for each game version.

## Stream Deck 0.7.0

The bundled plugin provides eight character keys and actions for Previous, Next, Next alert, Move up, Move down, Ignore/restore, Refresh and Launch/show. The Next alert key displays the pending count and focuses the oldest request. Character keys can place the number, name, class and alias independently on four lines. Portraits, badges, attention order, current application theme and language are synchronized automatically.

The bundled profile targets the standard 15-key Stream Deck. A window excluded from rotation remains directly accessible through its assigned character key.

## Quick installation

### Windows executable

Download the executable only from an official GitHub Release in this repository, verify its SHA-256 checksum when one is provided, place it in a permanent folder and run it. The standard executable does not include experimental Retro visual invitation detection.

Windows SmartScreen may warn about unsigned beta builds. Do not bypass that warning for a file obtained from anywhere else.

### From source

Requirements: Windows 10/11 64-bit and Python 3.12 or newer.

```powershell
git clone https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay.git
cd Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Install the Stream Deck plugin from **Application → Install Stream Deck plugin**, then accept the proposed profile.

## First steps

1. Start the manager and choose Unity or Retro.
2. Read the security warning, confirm that your copy came from the official repository, then open your Dofus clients and select **Refresh**.
3. Verify detected names and classes.
4. Drag characters into the desired order.
5. Create or load one profile per server, then optionally add an alias, portrait and badge through **Customize…**.
6. Test F5, F6, F7, F8 and Ctrl+Alt+R; direct access to windows 1 to 8 can be configured in Settings.
7. Save the profile.
8. Configure the overlay and notification under **Settings → In-game display**.

Default shortcuts:

| Action | Shortcut |
|---|---|
| Next character | F5 |
| Previous character | F6 |
| Ignore/restore current window | F7 |
| Refresh windows | Ctrl+Alt+R |

## Security and privacy

Dofus Window Manager does not read Dofus memory or network packets, inject code, send in-game commands, request Ankama credentials or upload portraits. Its Stream Deck bridge listens only on `127.0.0.1:32145`. Settings, profiles and logs remain under `%APPDATA%\DofusUnityWindowManager\`.

Run the manager and Dofus at the same Windows privilege level. On first launch, the application requires you to read a warning and confirm that the copy came from the official repository. If you already ran an unofficial copy, close it, disconnect the computer if necessary, change the Ankama and associated email passwords immediately from another trusted device, enable two-factor authentication, and run a full or offline antivirus scan. Read [SECURITY.md](SECURITY.md) and Ankama’s [anti-phishing guidance](https://support.ankama.com/hc/en-us/articles/201376953-Recognizing-and-Protecting-Yourself-from-Phishing).

## Build and test

```powershell
py -3.14 -m unittest discover -s tests -v
py -3.14 -m pip install -r requirements-dev.txt
py -3.14 -m ruff check .
py -3.14 build_exe.py
```

The PyInstaller output is `dist\DofusWindowManager.exe`. Stream Deck sources and build commands are under [`streamdeck-plugin`](streamdeck-plugin/README.md).

## Project status

Windows only. The project is community-made and is not affiliated with, endorsed by or sponsored by Ankama. Dofus, Dofus Retro, Ankama, and the bundled portraits and game icons under `assets/ankama` are the property of their respective owners. Those visual assets are not covered by the source code’s GPL-3.0 license; read the [asset notice](assets/ankama/NOTICE.md) before redistributing them.
