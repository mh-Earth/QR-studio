# QR Studio

A modern desktop QR code generator built with **Python** and **PySide6**. Design your QR code with full control over size, colors, shapes, gradients, captions and a center logo, then export it as PNG, JPG or SVG.

QR Studio ships with three themes (Light, Midnight and an animated **Jellyfish** theme) and remembers all your settings between sessions.

---

## Features

**Content types**
- Text / URL
- Wi-Fi (SSID, password, WPA / WEP / open)
- Email (address, subject, message)
- Phone number

**Design**
- Export size from 100 to 2000 px
- Adjustable quiet zone (white border), 0 to 12 modules
- Module shapes: Square, Rounded, Dots, Diamond
- Roundness and module spacing sliders
- Background corner radius
- Error correction: Low (7%), Medium (15%), Quartile (25%), High (30%)

**Colors**
- Solid or gradient foreground (diagonal, horizontal or vertical)
- Separate color for the three corner "eyes"
- Custom background color or a transparent background
- One-click swap of foreground and background
- Ready-made color presets

**Caption**
- Add text above or below the QR code (multi-line supported)
- Choose any installed font, size, bold / italic, alignment and color
- Adjustable space between the QR code and the caption, and between the caption and the image edge

**Logo**
- Place your own image in the center of the QR code
- Adjustable logo size and clear space around it, optional rounded corners
- Error correction is switched to High automatically while a logo is used

**App**
- Live preview that updates as you type
- Status bar with messages, contrast warnings, and QR version / module count / image size
- Light, Midnight and Jellyfish themes
- All settings are saved and restored on the next start
- **Reset** button to return to default design options

---

## Requirements

- Python **3.10 or newer**
- [PySide6](https://pypi.org/project/PySide6/)
- [qrcode](https://pypi.org/project/qrcode/)

## Installation

```bash
pip install PySide6 qrcode
```

## Running the app

```bash
python qr_generator_v2.py
```

Keep `app_icon.png` and `app_icon.ico` in the same folder as the script so the window icon loads.

---

## How to use

The settings are grouped into five tabs on the left. The preview and the **Save as...**, **Copy to clipboard** and **Reset** buttons are on the right.

| Tab | What it does |
|---|---|
| **Content** | Pick the content type and enter your data. |
| **Design** | Size, quiet zone, corner radius, module shape and spacing, error correction. |
| **Colors** | Foreground (solid or gradient), eye color, background, transparency, presets. |
| **Caption** | Text above or below the code, font, alignment, color and spacing. |
| **Logo** | Choose a center image, set its size, spacing and corner rounding. |

Use the **Theme** dropdown in the top-right corner to switch between Light, Midnight and Jellyfish.

### Exporting

Click **Save as...** and pick a format:

- **PNG**: supports transparency.
- **JPG**: no transparency; the background color is used.
- **SVG**: scalable vector output. Caption text is stored as live text, so the font needs to be installed on the machine that opens the SVG. A logo is embedded as an image.

**Copy to clipboard** copies the full-size image so you can paste it straight into other apps.

### Saved settings and Reset

Your options are saved automatically and restored the next time you open the app. This includes design options, colors, caption settings, the logo, the content you typed, the theme, and the window size and position.

- The **Wi-Fi password is never saved**, so you need to re-enter it each session.
- Settings are stored per user: in the registry on Windows (`HKEY_CURRENT_USER\Software\QRStudio`), in `~/.config/QRStudio` on Linux, and in a `.plist` file in `~/Library/Preferences` on macOS.
- **Reset** restores all design options (size, colors, shapes, caption settings, logo) to their defaults. It keeps the content you typed and your chosen theme.

---

## Tips for a QR code that scans reliably

- Keep strong **contrast** between the code and the background. QR Studio shows a warning in the status bar when contrast is low.
- Dark code on a light background is the most widely supported. Light-on-dark (inverted) codes are not read by every scanner.
- Keep a **quiet zone** of at least 2 to 4 modules around the code.
- When using a **logo**, keep it small (around 20% or less) and test the result with a phone before printing.
- Very high **module spacing** or very light gradient colors can make codes harder to read. Always test before printing or publishing.
- Longer content creates denser codes. Use a larger export size or lower error correction for very long text.

---

## Building a Windows executable

Install PyInstaller and run:

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name "QR Studio" --icon app_icon.ico --add-data "app_icon.png;." qr_generator_v2.py
```

The finished `QR Studio.exe` appears in the `dist` folder. On macOS or Linux, use `:` instead of `;` in the `--add-data` argument.

If Windows Explorer still shows the old icon after rebuilding, it is the icon cache. Rename the exe or restart Explorer.

---

## Project files

| File | Purpose |
|---|---|
| `qr_generator_v2.py` | The application. |
| `app_icon.ico` | Multi-size Windows icon (16 to 256 px), used for the exe. |
| `app_icon.png` | 512 px icon used for the window and taskbar. |

---

## Troubleshooting

**"Could not generate QR code" in the status bar**
The content is too long for a QR code at the selected error correction level. Shorten the content or choose a lower error correction level.

**The caption font looks different from what I chose**
The font list shows fonts installed on your system. If you open an exported SVG on another machine, it needs the same font installed.

**The logo does not appear after restarting**
The app remembers the logo's file path. If the image file was moved or deleted, the app starts without a logo. Choose it again on the **Logo** tab.

**The window or slider looks too large or small**
QR Studio follows your system display scaling. Adjust your operating system's scaling setting if needed.