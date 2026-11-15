# Take Back Your TV - Your Photos Instead of Ads

**One file that gets a coding agent to clean up your smart TV.** Your TV's home screen is mostly ads and
recommendations. Give [`agent.md`](agent.md) to Claude Code, Codex, Gemini CLI or Cursor, and the agent
turns off the preinstalled junk, replaces the home screen, and puts your own photos on it with a small
clock, your name and the four apps you open most.

There's no app to install and no API key. The playbook is the whole project.

## What you end up with

- **A home screen that's your photo.** A thin clock top left, a greeting with your name bottom left, and
  four app names as plain words bottom right. No tiles, no banners, no rows of things to buy.
- **Text that stays off faces.** The agent measures where the clock and text sit, finds the faces in each
  photo, and crops so nothing lands on anyone. Photos that can't be cropped cleanly are skipped.
- **Darker photos at night.** The set is sorted by brightness, so the bright ones stay out of the late
  rotation.
- **A screensaver that doesn't cut off heads.** Portraits and selfies are framed as cards before they go
  to the TV, so the slow zoom keeps every face on screen.
- **Fewer things running.** Ad, telemetry and unused preinstalled apps are switched off. Nothing is
  uninstalled, so every change can be undone.

## What you need

- An Android TV or Google TV: TCL, Sony, Hisense, Philips, Xiaomi, Chromecast with Google TV and similar.
  Samsung, LG and Roku TVs run different software and won't work.
- A computer on the same Wi-Fi as the TV.
- A coding agent that can run shell commands.
- A folder of photos.
- About an hour, with the remote nearby. The agent will ask you to accept a prompt on the TV and press a
  few buttons.

## How to use it

```sh
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/take-back-your-tv
```

Open your coding agent in that folder and say:

```text
Read agent.md and do this for my TV.
```

The agent starts by asking four things: which four apps you open most, what you use on the TV (voice
assistant, casting, live TV, preinstalled streaming apps), what name the greeting should show, and where
your photos are. Then it works through the steps in the file and checks in with you before anything risky.

## How it works

1. **Ask first.** Anything you say you use stays on.
2. **Connect** to the TV over ADB after you turn on debugging and accept the prompt.
3. **Clean up** in small batches, with a backup before the first change and a screenshot after each batch.
4. **Replace the home screen** with an open-source launcher built from source, and only then turn off the
   stock one.
5. **Prepare the photos** so the text never sits on a face.
6. **Build the screensaver frames.**
7. **Lock it back up:** debugging off, TV restarted, and the debugging port checked from the computer.

## Safety

- The agent disables apps and never uninstalls them. To bring one back on the TV, go to Settings > Apps >
  See all apps > Show system apps, pick the app and choose Enable.
- It leaves inputs, the tuner, remote pairing, the keyboard, the Play Store and Android's core packages
  alone.
- Your photos stay on your computer. Faces are detected locally and nothing is uploaded.
- You are still letting an agent change your TV. Read `agent.md` before you run it, and stay in the room.

## Good to know

- This was built and tested on one TV: a TCL Google TV on Android 11. Other Android TV and Google TV sets
  should behave the same way, but package names and menus differ by brand, which is why the agent asks
  before it disables anything.
- The words-only layout isn't a stock launcher theme. The playbook gives the agent the spec and the agent
  builds it into the launcher's source, so your result depends on how good your agent is.
- A firmware update can turn some apps back on. Run the playbook's clean-up step again if that happens.

## Credit

The playbook points the agent at [cleanyourtv](https://github.com/Gathin23/cleanyourtv) (MIT) for the
launcher and ADB tools. The layout, the photo method and the playbook are ours.
