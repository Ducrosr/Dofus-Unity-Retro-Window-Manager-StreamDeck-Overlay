# Dofus Window Manager

[Français](README.md) · **English** · [Español](README.es.md)

> [!NOTE]
> This translation was generated with AI assistance and may contain errors. Corrections are welcome through Issues or Pull Requests on the official repository.

A local Windows window manager for **Dofus Unity** and **Dofus Retro**, designed to make multi-account play easier to read and faster to control. It detects open Dofus windows, keeps their order and switches between them through global shortcuts, an overlay or a Stream Deck.

> [!WARNING]
> **This repository is the only official source:**
> <https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay>
>
> Never download Dofus Window Manager from a third-party website, private message or mirror. A modified copy could attempt to steal Ankama credentials, session tokens or personal data. The official application never asks for your Ankama password, two-factor authentication code or account access.
>
> Also read Ankama’s official guidance: **[Recognizing and protecting yourself from phishing](https://support.ankama.com/hc/en-us/articles/201376953-Recognizing-and-Protecting-Yourself-from-Phishing)**.

Version 2.20.0 is the current public beta. It brings together the multilingual interface, overlays, attention requests, portraits, official icons and Unity/Retro themes. The matching Windows executable is available from the [official v2.20.0-beta.1 Release](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/releases/tag/v2.20.0-beta.1).

## Main features

- native Dofus Unity and Retro window detection;
- next/previous character global shortcuts;
- ordering by buttons or drag and drop;
- per-character alias, custom or bundled class portrait, 39 official stat icons and 20 official profession icons;
- ignored windows remain bound to their Stream Deck keys but leave automatic rotation;
- saved JSON profiles and complete configuration backups;
- instant Unity/Retro switching;
- compact always-on-top mode;
- customizable switch notification, including content, position, duration and opacity;
- transparent, movable and resizable rotation overlay;
- orange `!` attention request indicator with optional subtle blinking in the app, overlay and Stream Deck;
- twelve themes available in both game modes: Standard, Bonta, Brakmar, Tribute, Gold and Steel, Belladone, Unicorn, Emerald Mine, Sufokia, Pandala, Wabbit and Retro;
- French by default, plus English and Spanish selected with one click;
- separate display reset that preserves profiles and character customization;
- optional official-release update check with no automatic download.

Standard is the default Unity theme and Retro is the default Retro theme. Every theme can be selected in either mode, and the application remembers one preference for each game version.

## Stream Deck 0.6.1

The bundled plugin provides eight character keys and actions for Previous, Next, Move up, Move down, Ignore/restore, Refresh and Launch/show. Character keys can place the number, name, class and alias independently on four lines. Portraits, badges, attention state, current application theme and language are synchronized automatically.

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
2. Open your Dofus clients and select **Refresh**.
3. Verify detected names and classes.
4. Drag characters into the desired order.
5. Optionally add an alias, portrait and badge through **Customize…**.
6. Test F5, F6, F7 and Ctrl+Alt+R.
7. Save a profile.
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

Run the manager and Dofus at the same Windows privilege level. Read [SECURITY.md](SECURITY.md) and Ankama’s [anti-phishing guidance](https://support.ankama.com/hc/en-us/articles/201376953-Recognizing-and-Protecting-Yourself-from-Phishing) before installing a binary obtained outside the official repository.

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
