// Optional live regression check. Sends only the synthetic cases below to Gemini.
import { suggest } from "../suggestions.mjs";
const groups = [
  {
    source: {
      before: "Attendance is online.",
      after: "Attendance is in person only.",
    },
    cases: [
      {
        id: "global",
        text: "Participants can attend from anywhere in the world.",
        expect: ["delete", "replace"],
        replaceContains: /in.person/i,
        avoids: /locally|local residents|nearby/i,
      },
      {
        id: "zoom",
        text: "Attendees will receive a Zoom link the day before the workshop.",
        expect: ["delete"],
      },
      {
        id: "mixed",
        text: "We will email a Zoom link; bring a laptop for the exercises.",
        expect: ["replace"],
        contains: /bring a laptop/i,
        avoids: /zoom|address|venue/i,
      },
      {
        id: "invite",
        text: "Join us online on October 12 at 10 AM for the workshop.",
        expect: ["replace"],
        contains: /October 12 at 10 AM/,
        avoids: /zoom|online/i,
      },
      {
        id: "history",
        text: "Last year's workshop was delivered online to 200 participants.",
        expect: ["keep"],
      },
      {
        id: "staff",
        text: "The organizing team will meet on Zoom on Monday to prepare the workshop.",
        expect: ["keep"],
      },
      {
        id: "recording",
        text: "Participants will receive a recording after the workshop.",
        expect: ["keep"],
      },
    ],
  },
  {
    source: {
      before: "The workshop takes place at 12 Market Street.",
      after:
        "The workshop has moved to a different venue; the address is not confirmed yet.",
    },
    cases: [
      {
        id: "address",
        text: "Please arrive at 12 Market Street by 9 AM.",
        expect: ["needs_info"],
      },
    ],
  },
  {
    source: {
      before: "The workshop is on October 12.",
      after: "The workshop is on October 19.",
    },
    cases: [
      {
        id: "date",
        text: "Doors open on October 12 at 9 AM; bring your confirmation email.",
        expect: ["replace"],
        contains: /October 19 at 9 AM.*confirmation email/i,
      },
    ],
  },
  {
    source: {
      before: "The workshop costs $99.",
      after: "The workshop is free.",
    },
    cases: [
      {
        id: "billing",
        text: "Enter your credit card details to pay the $99 registration fee.",
        expect: ["delete"],
      },
      {
        id: "mixedbilling",
        text: "Pay $99 and complete the accessibility questionnaire before attending.",
        expect: ["replace"],
        contains: /accessibility questionnaire/i,
        avoids: /99|pay|credit card/i,
      },
    ],
  },
];
let passed = 0,
  total = 0;
for (const group of groups) {
  const result = await suggest({
    source: group.source,
    passages: group.cases.map(({ id, text }) => ({ id, text })),
  });
  for (const c of group.cases) {
    const row = result.suggestions.find((s) => s.id === c.id);
    const pass =
      c.expect.includes(row?.action) &&
      (!c.contains || c.contains.test(row?.replacement)) &&
      (row?.action !== "replace" ||
        !c.replaceContains ||
        c.replaceContains.test(row.replacement)) &&
      (!c.avoids || !c.avoids.test(row?.replacement));
    total++;
    if (pass) passed++;
    console.log(JSON.stringify({ case: c.id, pass, ...row }));
  }
}
console.log(
  `${passed}/${total} synthetic editorial checks passed. This is a small live evaluation, not a general quality guarantee.`,
);
if (passed !== total) process.exitCode = 1;
