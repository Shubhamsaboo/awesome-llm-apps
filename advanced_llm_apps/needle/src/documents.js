export const documents = [
  {
    id: "stay",
    icon: "stay",
    name: "The weekend away",
    kind: "Travel & fine print",
    publisher: "FIELDNOTES STAYS",
    title: "A little escape.\nA little fine print.",
    subtitle: "Your guide to a slower weekend at The Wilder House.",
    tag: "BOOKING GUIDE",
    meta: "6 min read",
    suggestions: [
      "hidden fees",
      "can I bring my dog?",
      "what if my plans change?",
    ],
    sections: [
      {
        heading: "A place to press pause",
        paragraphs: [
          "Tucked between the redwoods and the coast, The Wilder House is a collection of quiet cabins made for long mornings. Your reservation includes a private cabin, breakfast for two, and access to the garden and walking trails.",
          "We want your stay to feel simple. Below is everything worth knowing before you pack your bags, from arrival times to the details of changing your reservation.",
        ],
      },
      {
        heading: "Your reservation",
        paragraphs: [
          "Check-in begins at 3 pm and check-out is by 11 am. Early arrivals are welcome to leave their bags at reception while exploring the grounds.",
          "The nightly rate includes breakfast and Wi-Fi. A property service charge of $35 per night is added at checkout. Parking is available for an additional $20 per vehicle, per night.",
          "A refundable security deposit of $150 is collected on arrival. It is returned within seven business days after departure, provided no damage is found.",
        ],
      },
      {
        heading: "When plans change",
        paragraphs: [
          "Reservations cancelled at least seven days before arrival receive a full refund of the room rate. For cancellations within seven days, the first night is non-refundable.",
          "A $25 administration charge is deducted from every cancellation refund, regardless of when the reservation was made. Third-party booking fees cannot be returned.",
          "You may move your stay once, at no extra charge, when requested more than 72 hours before arrival. New dates are subject to availability and any difference in room rate.",
        ],
      },
      {
        heading: "Bring your favorite company",
        paragraphs: [
          "Well-behaved dogs are welcome in our Garden Cabins. Please let us know before arrival so we can leave a water bowl and a blanket. Other animals are not permitted.",
          "A cleaning supplement of $45 per stay applies to reservations with a dog. Pets must remain on a lead in shared areas and cannot be left alone in the cabin.",
        ],
      },
      {
        heading: "Small comforts",
        paragraphs: [
          "Every cabin has a king-size bed, a reading nook, locally roasted coffee, and a record player. There are no televisions. We think the view more than makes up for it.",
          "Breakfast is served from 8 to 10 am. Vegetarian and gluten-free options are available. Please share any allergies with our team ahead of your visit.",
          "Need a hand? Our reception team is available every day from 7 am to 9 pm. For assistance outside these hours, use the phone number in your arrival email.",
        ],
      },
    ],
  },
  {
    id: "recipe",
    icon: "recipe",
    name: "Sunday pancakes",
    kind: "Recipes & substitutions",
    publisher: "THE SUNDAY TABLE",
    title: "Slow mornings.\nFluffy pancakes.",
    subtitle: "A forgiving recipe, with a few good swaps for an empty fridge.",
    tag: "FROM THE KITCHEN",
    meta: "4 min read",
    suggestions: [
      "what can replace the eggs?",
      "make it dairy free",
      "can I prepare this ahead?",
    ],
    sections: [
      {
        heading: "A weekend ritual",
        paragraphs: [
          "These pancakes are tender in the middle and lightly crisp at the edges. The batter takes ten minutes to bring together and makes enough for four people. Serve warm with berries and maple syrup.",
        ],
      },
      {
        heading: "What you’ll need",
        paragraphs: [
          "Gather 200 g of plain flour, two tablespoons of sugar, two teaspoons of baking powder, a pinch of salt, two eggs, 250 ml of milk, and two tablespoons of melted butter.",
          "For a batch without eggs, use half a mashed banana for each egg. Alternatively, combine one tablespoon of ground flaxseed with three tablespoons of water per egg and leave it for five minutes. The banana version will taste a little sweeter.",
          "Oat milk works in place of regular milk at the same quantity. Swap the melted butter for a neutral oil to make the batter entirely dairy-free.",
        ],
      },
      {
        heading: "Mix gently",
        paragraphs: [
          "Whisk the dry ingredients in one bowl and the wet ingredients in another. Fold them together until just combined. A few small lumps are welcome; overmixing makes pancakes tough.",
          "Let the batter rest for five minutes while the pan warms. Cook over medium heat, turning each pancake when bubbles appear on the surface and the edges look set.",
        ],
      },
      {
        heading: "Save some for later",
        paragraphs: [
          "You can mix the dry ingredients the night before and keep them covered. Add the wet ingredients just before cooking for the best rise.",
          "Cooked pancakes keep in the refrigerator for three days or in the freezer for two months. Reheat in a toaster or a low oven rather than microwaving if you prefer crisp edges.",
        ],
      },
    ],
  },
  {
    id: "thread",
    icon: "thread",
    name: "The launch thread",
    kind: "Work & conversations",
    publisher: "ACME / PRODUCT TEAM",
    title: "One launch.\nA lot of messages.",
    subtitle: "The decisions you remember, somewhere in the conversation.",
    tag: "TEAM CONVERSATION",
    meta: "5 min read",
    suggestions: [
      "what price did we agree on?",
      "who is doing the landing page?",
      "what is blocking launch?",
    ],
    sections: [
      {
        heading: "Monday · Getting aligned",
        paragraphs: [
          "Maya · 9:04 AM : Before we announce anything, we need to agree on the Starter tier. I suggested $19 last week, but support thinks that won’t cover onboarding.",
          "Alex · 9:18 AM : Let’s go with $29 per month for Starter, with a 14-day trial and no card required. The team agreed to this on today’s call. Annual billing can wait until next month.",
          "Jordan · 9:32 AM : I’ve updated the comparison chart in the shared folder. The old presentation still says $19; please don’t use that version.",
        ],
      },
      {
        heading: "Tuesday · Who owns what",
        paragraphs: [
          "Maya · 10:12 AM : Priya is taking the landing page, including the pricing section. Alex owns the welcome email. I’ll review both on Thursday.",
          "Priya · 10:25 AM : Got it. The page is almost done. I need the final product screenshots before I can finish the hero section.",
          "Sam · 11:03 AM : I can export the screenshots tomorrow, once the new onboarding flow is on staging.",
        ],
      },
      {
        heading: "Wednesday · A dependency to watch",
        paragraphs: [
          "Sam · 2:10 PM : Staging is still on the old build. The deployment is blocked by the authentication regression; engineering is investigating.",
          "Priya · 2:21 PM : Then the screenshots and final landing page are blocked too. I can finish the layout with placeholders, but we shouldn’t announce until the real flow works.",
          "Alex · 3:06 PM : Welcome email draft is ready. I removed the annual plan mention and used the agreed $29 monthly price.",
        ],
      },
      {
        heading: "Thursday · Next check-in",
        paragraphs: [
          "Maya · 9:00 AM : Let’s check the authentication fix at noon. If it passes, Sam can capture the screenshots and Priya can finish the page. No announcement before we verify signup.",
          "Jordan · 9:15 AM : I’ll take notes and update the launch checklist after the check-in.",
        ],
      },
    ],
  },
];
export function getBlocks(doc) {
  let i = 0;
  return doc.sections.flatMap((section) =>
    section.paragraphs.map((text) => ({
      id: `b${i++}`,
      text,
      heading: section.heading,
    })),
  );
}
