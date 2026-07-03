export interface Testimonial {
  name: string;
  /** Display date, e.g. "December 18, 2024". */
  date: string;
  /** Machine date for <time datetime>, e.g. "2024-12-18". */
  iso: string;
  message: string;
  /** Strongest quotes, pulled above the grid (§6.6). */
  featured?: boolean;
}

// Night-shift thank-you notes from Scripps Mercy, 2022–2025. The recognition page
// derives its counts (unique colleagues, year span) from this array so the summary
// can never drift from the data.
export const testimonials: Testimonial[] = [
  {
    name: 'Kayla',
    date: 'July 30, 2025',
    iso: '2025-07-30',
    message: 'Thank you for always going above and beyond!! You are very much appreciated!!',
  },
  {
    name: 'Mindy',
    date: 'July 10, 2025',
    iso: '2025-07-10',
    message:
      'Thanks for all of your help with the late night recognition event for Mercy San Diego 135th Birthday and "A" Leapfrog Score celebration! There is a lot less help and support for the evening events and your work together helped make it a success!',
  },
  {
    name: 'Michael',
    date: 'July 8, 2025',
    iso: '2025-07-08',
    message: "It's always a joy working when you're on. You always take care of the night shift.",
  },
  {
    name: 'Deborah',
    date: 'May 6, 2025',
    iso: '2025-05-06',
    message:
      'Thank you soooooo much for assisting in the sanitation area last night!! Your willingness to "just step in" shows you are a team player and willing to help where needed and was much appreciated by me.',
  },
  {
    name: 'Laura',
    date: 'February 26, 2025',
    iso: '2025-02-26',
    message:
      'Hey Nate! Thank you for all you do for 3rd shift EVS! We always look forward to you being in the kitchen. You are appreciated :)',
  },
  {
    name: 'Jeff',
    date: 'December 18, 2024',
    iso: '2024-12-18',
    featured: true,
    message:
      'I wanted to take a moment to thank you for your amazing support during the Cookies and Cocoa evening event on December 17th. We had an amazing turnout, and we ran out of hot cocoa about half way through. You immediately took action and began making more. Your quick action and adaptability saved the event for hundreds of night-shift employees that would have gone without had it not been for you. You are a true value to the Food & Nutrition department, Mercy and Scripps as a whole.',
  },
  {
    name: 'Patricia',
    date: 'November 20, 2024',
    iso: '2024-11-20',
    featured: true,
    message:
      'I just want to give a big Thanks to Nathan in food service for having "Excellent" customer service. Due to working Noc shift we really miss out on the day shift cafeteria experience, but when he is working, he makes sure that we have plenty of options to choose from by having everything fully stocked, always organized and the grill is always open. He is very professional, respectful and always has a positive attitude. You are most definitely the MVP!',
  },
  {
    name: 'Norma',
    date: 'November 7, 2024',
    iso: '2024-11-07',
    message:
      'Nathan, Thank you for your passion for customer service. Your dedication is an inspiration in the workplace. We are grateful for your help and support to the night shift!',
  },
  {
    name: 'Alicia',
    date: 'October 11, 2024',
    iso: '2024-10-11',
    featured: true,
    message:
      "I've had the pleasure of observing Nate in the cafeteria for quite a while now, and he consistently brings a smile to work every day, ready to serve. While I wait for my food, I often hear fellow staff members praising his exceptional service. When Nate takes a day off, his absence is felt throughout the entire hospital. He embodies the spirit of going above and beyond. Thank you, Nate. We are all truly grateful for you!",
  },
  {
    name: 'Leanne',
    date: 'September 11, 2024',
    iso: '2024-09-11',
    message:
      "I'd like to appreciate Nate for how hard he works to cook for our overnight hospital staff! He is always taking care of us, and so many of us night shift staff are grateful for his kindness.",
  },
  {
    name: 'Marivic',
    date: 'May 6, 2024',
    iso: '2024-05-06',
    message:
      "Nathan, you are always friendly to people and the people you serve. We are always happy to see you when you are on duty. Because I know the food will be extra good. You give great quality service and meet customer's expectations. You are only one man but can tackle many orders like a boss. And fast service. I appreciate your hard work and dedication to your duties.",
  },
  {
    name: 'Norma',
    date: 'March 19, 2024',
    iso: '2024-03-19',
    message:
      'Nathan, I am genuinely thankful for all the things you do for the night shift. Thank you for your kindness, generosity and the great service you provide to all of us!',
  },
  {
    name: 'Jed',
    date: 'February 11, 2024',
    iso: '2024-02-11',
    message:
      'Nathan always finds a way to liven up the mood during our meal breaks. Everything from the music he plays to his positive & warm demeanor. Not to mention his culinary skills! Thank you for everything you do Nathan, we appreciate your hard work!',
  },
  {
    name: 'Erin',
    date: 'February 4, 2024',
    iso: '2024-02-04',
    message:
      "Nate, Thank you from all of us in the Emergency Dept for always showing up in the middle of the night to bring us yummy food, fed to us from your heart, great music and immaculate vibes! The heart shaped pancakes the other night really took the cake. Thank you for always going above and beyond, making sure night shift has access to all that Colors cafe has to offer, including the grill, which we miss so much when you're not there.",
  },
  {
    name: 'Christine',
    date: 'February 24, 2023',
    iso: '2023-02-24',
    message:
      'Nathan I want to let you know how much I appreciate you keeping the cafeteria offerings available to us night crew workers. You are the only one who provides us with variety and keeps the hot station open, so we have more choices at night. It makes a huge difference. I commend you for the extra work that entails, but it really means a lot to all the graveyard shift workers.',
  },
  {
    name: 'Christine',
    date: 'May 8, 2022',
    iso: '2022-05-08',
    message:
      'Nathan is the BEST!!! He is a fast and efficient worker in addition to being such a kind, good-natured and funny guy. Even when he is super busy he remains friendly and attentive. I look forward to seeing him whenever I visit the cafeteria on my overnight shift and always walk away with a huge smile on my face. Nathan is truly a wonderful employee deserving of high praise.',
  },
  {
    name: 'Megan',
    date: 'April 16, 2022',
    iso: '2022-04-16',
    message:
      "I'd like to take this time to appreciate Nathan for having hot foods available to us. I used to work days and one thing that I missed is the hot food. Now that I work nights, I feel excited to know that Nathan is a part of your staff. It really makes a difference in morale when there is hot food and he makes the cafe lively at night. He definitely knows what he is doing! I don't think people on day shift really understand how much value you bring to us on nights!",
  },
  {
    name: 'Ivan',
    date: 'January 19, 2022',
    iso: '2022-01-19',
    message:
      "Hi Nate! Just wanted to say thank you again for always being such a great & positive person, especially to those of us in the night shift, where positivity has been hard to find lately. You're always so kind and helpful, with a wonderful attitude that we should ALL have more of. It's always nice to see you there for us night shift peeps. You rock!",
  },
];
