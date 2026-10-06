#!/usr/bin/env python3
"""Drop footage / b-roll ideas onto the timeline that is currently open in DaVinci Resolve.

How to run it
-------------
Easiest: in Resolve, Workspace > Console, switch the console to "Py3", then paste
this whole file in and hit Enter. `resolve` already exists in that console.

From a terminal instead, make sure Resolve's scripting module is importable
(RESOLVE_SCRIPT_API / RESOLVE_SCRIPT_LIB set, or run with Resolve's bundled
python) and then: python3 footage_ideas.py

Edit IDEAS below to your own list. Everything else has a working default.
"""

# ---------------------------------------------------------------- settings --

# One idea per entry. (short label, longer note). The label is what you see on
# the timeline ruler; the note is what you read when you open the marker.
IDEAS = [
    ("Establishing wide", "Locked-off wide of the location before anyone enters frame. Buys you an out of any cut."),
    ("Hands insert", "Tight on hands doing the task — keys, tools, phone, coffee. Cheapest cutaway that always works."),
    ("Face, no dialogue", "Hold on the face two beats after they stop talking. Reaction beats carry the edit."),
    ("Over-the-shoulder", "OTS looking into whatever they're looking at. Gives you a clean eyeline match."),
    ("Detail / texture", "Macro on surface detail — fabric, rust, grain, condensation. Good for breathing room."),
    ("Movement through frame", "Subject enters and exits frame. Natural in/out points for a transition."),
    ("Environment ambience", "Slow pan or push on the space with nobody in it. Sets mood, hides a jump cut."),
    ("Practical light", "Lamp, screen glow, window. Something that motivates your key light in the wide."),
    ("Foreground obstruction", "Shoot past a doorway, plant, or crowd. Adds depth and a layer to cut against."),
    ("Reverse angle", "Same beat from the opposite side of the line. Emergency fix for a bad take."),
    ("Time passing", "Clouds, traffic, shadow moving, clock. Lets you compress a chunk of the scene."),
    ("Exit / button shot", "The last thing left behind after the subject leaves. Ends the sequence cleanly."),
    ("Hoe opener: club legacy", "Molokai Hoe opener. Between the first race and then came she'll vaa, talk about the pretty fierce legacy between "
                    "local clubs throughout the state that pushed the sport of outrigger canoe paddling globally "
                    "... then came Tahiti."),
]

MODE = "markers"   # "markers" | "titles" | "both"
PLACEMENT = "clip" # "clip"  -> one idea per clip on the source track
                   # "even"  -> spread ideas evenly across the whole timeline
SOURCE_TRACK = 1   # which video track to read clips from when PLACEMENT == "clip"
TITLE_TRACK = None # video track for Text+ in "titles"/"both" mode. None = new top track
MARKER_COLOR = "Yellow"
MARKER_DURATION = 1
CYCLE_IDEAS = True # reuse the list from the top if there are more clips than ideas

# ------------------------------------------------------------------- setup --

def get_resolve():
    try:
        return resolve  # noqa: F821 — predefined inside Resolve's console
    except NameError:
        pass
    try:
        import DaVinciResolveScript as dvr
    except ImportError:
        raise SystemExit(
            "Couldn't import DaVinciResolveScript. Run this from Resolve's console "
            "(Workspace > Console, Py3 tab) or set RESOLVE_SCRIPT_API and "
            "RESOLVE_SCRIPT_LIB first."
        )
    app = dvr.scriptapp("Resolve")
    if app is None:
        raise SystemExit("Resolve isn't running, or external scripting is off "
                         "(Preferences > System > General > External scripting using: Local).")
    return app


def frames_to_tc(frame, fps):
    fps = int(round(fps)) or 24
    frame = int(frame)
    h, rem = divmod(frame, 3600 * fps)
    m, rem = divmod(rem, 60 * fps)
    s, f = divmod(rem, fps)
    return "%02d:%02d:%02d:%02d" % (h, m, s, f)


# ------------------------------------------------------------------ actions --

def pick_frames(timeline, count_hint):
    """Return [(absolute_frame, clip_name_or_None), ...] where ideas should go."""
    start, end = timeline.GetStartFrame(), timeline.GetEndFrame()

    if PLACEMENT == "clip":
        items = timeline.GetItemListInTrack("video", SOURCE_TRACK) or []
        if items:
            return [(it.GetStart(), it.GetName()) for it in items]
        print("No clips found on V%d — falling back to even spacing." % SOURCE_TRACK)

    n = max(1, count_hint)
    span = max(1, end - start)
    step = span // n
    return [(start + i * step, None) for i in range(n)]


def add_markers(timeline, spots):
    added = skipped = 0
    for frame, clip_name, label, note in spots:
        # AddMarker takes a frame offset from the timeline's start, not an absolute frame.
        rel = int(frame - timeline.GetStartFrame())
        body = note if not clip_name else "%s\n\n(on: %s)" % (note, clip_name)
        for nudge in range(0, 25):  # a frame can only hold one marker; step off a collision
            if timeline.AddMarker(rel + nudge, MARKER_COLOR, label, body, MARKER_DURATION):
                added += 1
                break
        else:
            skipped += 1
            print("  ! no free frame near %d for %r" % (rel, label))
    print("Markers: %d added, %d skipped." % (added, skipped))


def add_titles(timeline, spots, fps):
    track = TITLE_TRACK
    if track is None:
        if not timeline.AddTrack("video"):
            print("Couldn't add a video track for the titles.")
            return
        track = timeline.GetTrackCount("video")
        print("Titles going on new track V%d." % track)

    placed = 0
    for frame, _clip_name, label, note in spots:
        timeline.SetCurrentTimecode(frames_to_tc(frame, fps))
        item = timeline.InsertFusionGeneratorIntoTimeline("Text+")
        if not item:
            print("  ! Text+ insert failed at %s" % frames_to_tc(frame, fps))
            continue
        if not set_text(item, "%s\n%s" % (label, note)):
            print("  ~ inserted a Text+ at %s but couldn't write into it; type it by hand."
                  % frames_to_tc(frame, fps))
        placed += 1
    print("Text+ titles: %d placed." % placed)


def set_text(item, text):
    comp = item.GetFusionCompByIndex(1)
    if not comp:
        return False
    tools = comp.GetToolList(False, "TextPlus") or {}
    if not tools:
        return False
    for tool in tools.values():
        tool.SetInput("StyledText", text)
    return True


# --------------------------------------------------------------------- main --

def main():
    app = get_resolve()
    project = app.GetProjectManager().GetCurrentProject()
    if not project:
        raise SystemExit("No project open.")
    timeline = project.GetCurrentTimeline()
    if not timeline:
        raise SystemExit("No timeline open. Open the one you want annotated and run again.")

    try:
        fps = float(project.GetSetting("timelineFrameRate"))
    except (TypeError, ValueError):
        fps = 24.0

    print("Timeline: %s  (%.3f fps)" % (timeline.GetName(), fps))

    frames = pick_frames(timeline, len(IDEAS))
    if not CYCLE_IDEAS:
        frames = frames[:len(IDEAS)]

    spots = []
    for i, (frame, clip_name) in enumerate(frames):
        label, note = IDEAS[i % len(IDEAS)]
        spots.append((frame, clip_name, label, note))

    print("Placing %d ideas." % len(spots))
    if MODE in ("markers", "both"):
        add_markers(timeline, spots)
    if MODE in ("titles", "both"):
        add_titles(timeline, spots, fps)
    print("Done.")


main()
