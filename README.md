# Metashape Scripts

Python scripts for [Agisoft Metashape Pro](https://www.agisoft.com/).

- **[Reef/](Reef/)**: for reef-scale underwater photogrammetry.
- **[CoralFragment/](CoralFragment/)**: for individual coral fragments photographed on Christine's automated turntable.

Each folder has its own README describing what the scripts do.

## Using the scripts

Each script adds a menu item under **Tools** in Metashape. There are two ways to load them.

### Option 1: Paste into the Metashape Console (temporary)

1. In Metashape, open the console: **View → Console**.
2. Open the script file in a text editor, copy all of it, and paste it into the console.
3. Press **Enter**. The script's menu item appears under **Tools**.

> **The menu item will be gone after restarting Metashape.** You'll need to paste the script in again each time. Use Option 2 if you use the script regularly.

### Option 2: Add to the Metashape scripts folder (permanent)

Metashape runs every script in a special `scripts` folder when it starts, so these menu items will always be in the **Tools** menu.

1. Quit Metashape.
2. Open the scripts folder (see below). If the `scripts` folder doesn't exist, create it.
3. Copy the `.py` files you want into it.
4. Start Metashape. The menu items appear under **Tools**.

To remove a script, delete it from the folder and restart Metashape.

#### Mac

The folder is:

```
~/Library/Application Support/Agisoft/Metashape Pro/scripts/
```

The `Library` folder is hidden by default. To get there:

1. In Finder, choose **Go → Go to Folder…** (or press **⌘ Cmd + Shift + G**).
2. Paste `~/Library/Application Support/Agisoft/Metashape Pro/` and press **Enter**.
3. Open the `scripts` folder, or create one called `scripts` if it isn't there.

#### Windows

The folder is:

```
C:\Users\<your user name>\AppData\Local\Agisoft\Metashape Pro\scripts\
```

The `AppData` folder is hidden by default. To get there:

1. Open File Explorer.
2. Click in the address bar at the top, paste `%LOCALAPPDATA%\Agisoft\Metashape Pro` and press **Enter**.
3. Open the `scripts` folder, or create one called `scripts` if it isn't there.
