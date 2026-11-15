# Take Back Your TV

**One file that gets a coding agent to clean up your smart TV.** Give [`agent.md`](agent.md) to Claude
Code, Codex, Gemini CLI or Cursor. The agent turns off the preinstalled junk, replaces the ad-filled home
screen, and puts your own photos on it with a small clock, your name and the four apps you open most.

There's no app to install and no API key.

## What you get

- A home screen that's your photo, with a thin clock, a greeting and four app names as plain words.
- Text that never sits on a face. The agent crops each photo around the people in it.
- A screensaver that doesn't cut off heads in portraits and selfies.
- Ad, telemetry and unused preinstalled apps switched off. Nothing is uninstalled.

## What you need

- An Android TV or Google TV (TCL, Sony, Hisense, Philips, Xiaomi, Chromecast with Google TV). Samsung,
  LG and Roku won't work.
- A computer on the same Wi-Fi, a coding agent that can run shell commands, and a folder of photos.
- About an hour, with the remote nearby.

## How to use it

```sh
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/take-back-your-tv
```

Open your coding agent in that folder and say:

```text
Read agent.md and do this for my TV.
```

It asks which four apps you open most, what you use on the TV, what name to show and where your photos
are. Then it connects over ADB, cleans up in small batches, swaps the home screen, prepares the photos and
turns debugging back off.

## Good to know

- Everything can be undone. To bring an app back, go to Settings > Apps > See all apps > Show system apps
  and choose Enable.
- Your photos stay on your computer. Faces are detected locally.
- This was built and tested on one TV, a TCL Google TV on Android 11. Menus and package names differ by
  brand, so read `agent.md` first and stay in the room while it runs.
- The words-only layout isn't a stock theme. The agent builds it from the spec, so results depend on your
  agent.

The playbook uses [cleanyourtv](https://github.com/Gathin23/cleanyourtv) (MIT) for the launcher and ADB
tools.
