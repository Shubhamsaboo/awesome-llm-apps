# Take Back Your TV

Your smart TV's home screen is mostly ads. This file gets a coding agent to fix that: it turns off the
junk, swaps the home screen, and puts your own photos on it with a small clock, your name and your four
favorite apps.

**To use it:** give this file to a coding agent (Claude Code, Codex, Gemini CLI, Cursor) and say "do this
for my TV". You'll need:

- An Android TV or Google TV (TCL, Sony, Hisense, Philips, Xiaomi, Chromecast with Google TV and so on).
  Samsung, LG and Roku TVs run different software and won't work. Fire TV isn't covered.
- The TV and your computer on the same Wi-Fi.
- A folder of photos you'd like to see on the TV.
- About an hour, and the remote nearby. The agent will ask you to press a few things.

Everything below is for the agent.

---

## Ground rules

You're changing someone's TV. These come first.

- Disable, never uninstall: `pm disable-user --user 0 <package>`, one package at a time. `pm enable` must
  be able to undo everything you do. No root, no flashing.
- Back up before the first change: the full package list, what's already disabled, `getprop`, and the
  settings. Keep a list of everything you turn off.
- Don't touch what makes it a TV: HDMI inputs and the tuner, remote and Bluetooth pairing, the on-screen
  keyboard, the Play Store and Play Services, Settings, System UI, and Android's core packages. If you
  can't tell what a package does, run `dumpsys package <name>` and ask.
- Never open a factory or service-menu app, even to look.
- Their photos, backups and screenshots stay on their computer. Don't upload them and don't commit them.
- If the TV refuses something, stop and say so. Don't retry in a loop.

## 1. Ask first

Before connecting, ask these in one go:

1. Which four apps do you open most? They go on the home screen.
2. Which of these do you use: voice assistant, Chromecast or AirPlay, live TV, any streaming apps that
   came preinstalled? Anything they use stays on.
3. What name or names should the greeting show?
4. Where's the photo folder?

## 2. Connect

Have them turn on Developer options (Settings > System > About, then press OK on the build number seven
times; it's labelled "Android TV OS build" on Google TV and "Build" on older sets) and then USB debugging
or Network debugging. Find the TV on the network, connect with `adb connect <tv ip>:5555`, and
ask them to accept the prompt on the TV. Check the model, Android version and screen size before going on.

## 3. Clean up

Work in small batches, safest first, with a screenshot after each:

1. The manufacturer's ad, content and recommendation apps
2. Telemetry and preloaded apps
3. Google apps they said they don't use
4. Streaming apps they said they don't watch

Keep one list file per batch so any batch can be undone alone. Leave the firmware updater on unless they
ask otherwise, and tell them if a telemetry package looks like it also carries the updater.

Reboot once at the end and check that everything is still off.

## 4. Replace the home screen

Use an open-source launcher you can build from source. [cleanyourtv](https://github.com/Gathin23/cleanyourtv)
(MIT) is a good base and comes with ADB tools for backup, disable and restore. Don't install a prebuilt
APK from somewhere random.

Two things can lock people out here:

- Install the new launcher and confirm it is Home before disabling the stock one. A TV with no home
  screen is a bad afternoon.
- On Google TV, the setup wizard can own the saved Wi-Fi networks. Disable it while it does and the TV
  drops off Wi-Fi and you lose ADB. Have them forget the network and join it again first, and check for
  old saved networks that are out of range.

### The layout

| What | Where | Details |
|---|---|---|
| Clock | Top left | Large and thin (about 74sp, extra-light), no AM/PM |
| Date | Under the clock | Small, spaced out (13sp) |
| Buttons | Top right | Icons only: settings, inputs, app library |
| Greeting | Bottom left | "Good evening" in small text, the name in serif italic (about 37sp), then the photo's caption |
| Apps | Bottom right | The four app names as plain words (18sp). No tiles or icons. The focused one is bright with an underline, the others are at about 55% |

- One row of four apps. Everything else goes in the app library.
- No dark overlay on the photo, no glow, no bar behind the apps. Dimming the whole picture makes faces
  look muddy.
- Check the longest app name on the real screen. Mock-ups don't show when a word gets cut off.
- If removing tile backgrounds leaves a faint box behind the focused word, remove the tile's outline too.

Show three or four mock-ups on their own photos before you build anything, and let them choose.

## 5. Prepare the photos

The text must never land on someone's face.

1. Take a screenshot of the finished home screen and measure where the clock, greeting, app names and
   buttons sit.
2. Find the faces in each photo on the computer, using the operating system's own tools.
3. For each photo, pick a 16:9 crop where no face is under any of those areas. If you can't get below
   about 5% of a face covered, skip that photo. Portraits rarely work on Home; save them for the
   screensaver.
4. Darken the background slightly more than the people, and add a soft gradient in the corners where the
   text sits.
5. Sort the photos by brightness so that only the darker ones show at night.
6. Captions are a place and a month. If you're guessing the place from GPS data, say it's a guess. Don't
   send coordinates to an online service.

Rotate the photos every five minutes or so.

## 6. Screensaver

A photo screensaver that zooms and drifts only keeps the middle of each picture on screen, roughly the
central 78%. Portraits and selfies sent in as they are lose the tops of heads.

Build each frame at the TV's resolution first:

- Landscapes: crop around the faces.
- Portraits: put them on a blurred copy of themselves as a framed card, or two side by side.
- Keep every face inside the safe middle area.
- About 20 seconds per photo.

Then start the screensaver and watch a few photos go by before saying it works.

## 7. Lock it back up

- Turn off USB and Network debugging, and revoke the debugging authorizations.
- Have them restart the TV.
- From the computer, check that port 5555 refuses the connection.
- Leave them a short note: what was turned off, how to turn one app back on (Settings > Apps > See all
  apps > Show system apps > Enable), and how to undo everything.

## How to work

- Mock-ups before code. Taste is theirs, not yours.
- Test on the TV before you say it's done. It compiling doesn't count.
- Keep testing quick. One check that covers every photo is better than watching them rotate for an hour.
- One change at a time: push it, look at it, move on.
- Screenshots come back empty while a streaming app is playing. That's normal. Don't press Home on
  someone who is watching.
- Tell them what you didn't check.
