"""
Seed the vector database with ALL winning script examples.
Run this once to populate the database with proven viral scripts.

Usage:
    cd backend
    python -m app.db.seed_winning_scripts
"""

from app.db.storage import add_script_to_db
from app.utils.skeleton_utils import generate_skeleton
from app.schemas.enums import ScriptMode, HookType


# Map string values to enums
MODE_MAP = {
    "informational": ScriptMode.INFORMATIONAL,
    "listical": ScriptMode.LISTICAL,
}

HOOK_TYPE_MAP = {
    "shock": HookType.SHOCK,
    "question": HookType.QUESTION,
    "negative": HookType.NEGATIVE,
    "story": HookType.STORY,
}


WINNING_SCRIPTS = [
    # 1. Samay Raina's Latent App
    {
        "title": "Samay Raina Latent App",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"Samay Raina is a pure marketing genius. What he just did blew my mind."

HOOK 2:
"Samay Raina beat Netflix and Hotstar with just one Instagram story."

HOOK 3:
"This comedian's app became India's most downloaded in 24 hours. Zero marketing."

HOOK 4:
"One Instagram story. Number one on App Store. Here's how Samay Raina did it."

HOOK 5:
"Indian comedian beats billion-dollar streaming giants with a single post."

## FINAL SCRIPT

"Samay Raina beat Netflix and Hotstar with just one Instagram story."

He casually dropped an app for his show "India Got Latent" and it instantly became the most downloaded entertainment app in India.

But here's what's fascinating.

People are going crazy to download an app to watch something that's already free on YouTube.

The psychology behind this? Pure genius.

His show is already crushing it with 20 million views per episode. Why? Because he does what TV networks won't. Poonam Pandey as judge, Rakhi Sawant uncensored, guests TV channels wouldn't dare touch.

So when he simply posted "Hey, dropped an app for the show," people went crazy.

This isn't random. It's called the Velvet Rope Effect.

Within 24 hours, he hit number one on the App Store. No marketing campaigns. No promotions. Just one story.

Look at the contrast: Netflix begs "Please download our app." Hotstar shouts "We have IPL!" Samay just whispers "Want more Latent?"

Boom. Number one.

Hit follow for more psychology insights nobody's talking about. Save this marketing masterclass for later."""
    },

    # 2. Milaf Cola
    {
        "title": "Milaf Cola",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"This startup just turned fruit into a drink that's become Coca-Cola's biggest competition."

HOOK 2:
"Gen Z is abandoning Coca-Cola, and this ancient fruit-based drink is the reason why."

HOOK 3:
"For the first time in 137 years, Coca-Cola is actually scared of a competitor."

HOOK 4:
"This drink is made entirely from dates. Saudi Arabia just backed it with 2.5 billion dollars."

HOOK 5:
"A date-based cola is threatening Coca-Cola's 137-year reign. India could be next."

## FINAL SCRIPT

"For the first time in 137 years, Coca-Cola is actually scared of a competitor."

And it's not Pepsi.

Now here's the crazy part. This drink is made entirely from dates. Yes, the fruit.

They've turned dates into a cola that people are calling 'liquid sunshine' - with zero added sugar.

Saudi Arabia just backed this with 2.5 billion dollars, and they're selling it for just 70 cents per can.

Gen Z is already loving it. 33% are ditching sugary sodas completely.

But here's why I'm sharing this. This is huge for India.

With companies like Reliance's Campa Cola and new startups, we have a massive opportunity.

Think about it: India is becoming more health-conscious than ever. We have the manufacturing capability, the market size, and guess what? We even have our own date farms.

And with Zepto, Blinkit, and quick commerce platforms, any new beverage brand can reach millions of Indians in minutes.

The next big natural cola brand could come from India.

For entrepreneurs watching this - the blueprint is right here. The market is ready.

Follow for more game-changing business opportunities."""
    },

    # 3. Kunal Bahl
    {
        "title": "Kunal Bahl Shark Tank",
        "mode": "informational",
        "hook_type": "story",
        "content": """## HOOK OPTIONS

HOOK 1:
"Meet the shark of sharks, Kunal Bahl who turned 50 lakhs into 200 plus crores."

HOOK 2:
"This new Shark turned 50 lakhs into 200 plus crores and invested in over 280 startups."

HOOK 3:
"One 50 lakh investment turned into 200 crores. Here's the investor behind it."

HOOK 4:
"He invested 50 lakhs in Ola Cabs. Today that's worth over 200 crores."

HOOK 5:
"The Shark of all Sharks invested in 280 startups. His story starts with Snapdeal."

## FINAL SCRIPT

"This new Shark turned 50 lakhs into 200 plus crores."

Post that he invested in over 280 startups and god knows how much money he has made. He is the Shark of all the sharks.

Here's why.

Meet Kunal Bahl. In 2010, he started with a simple idea. A website selling daily deals and discount coupons.

But then he made a bold move that changed everything. He completely transformed his business model. Turned his company Snapdeal into an e-commerce giant.

And guess what? It worked. The company exploded in growth. Hit a massive 54,000 crore valuation.

While everyone was focused on his success with Snapdeal, Kunal was quietly making another move.

He spotted a small startup that nobody believed in. His investment? Just 50 lakhs in a company called Ola Cabs.

Here's where it gets crazy. That one 50 lakh investment? Turned into over 200 crores.

But Kunal wasn't done. Through his fund Titan Capital, he went on to spot unicorns before anyone else. Razorpay before it became huge. Mamaearth before it became a household name. Urban Company before it revolutionized services.

Today's numbers? He's backed more than 280 startups. More than any other shark on the show. Many giving 100x returns.

What makes him different? He's been in the founder's and investor's shoes both.

Do follow me for more such insightful stories."""
    },

    # 4. Mukesh Ambani's 1L Crores Land
    {
        "title": "Mukesh Ambani Land Deal",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"This land is worth 1L crores but Ambani bought it for just 2200 crores. And that too legally."

HOOK 2:
"Mukesh Ambani bought 100,000 crore rupees worth of land for just 2,200 crore rupees."

HOOK 3:
"Ambani acquired land bigger than 4,000 football fields for 98% discount. Here's how."

HOOK 4:
"Mukesh Ambani's genius move turned 2,200 crores into 1 lakh crore asset overnight."

HOOK 5:
"This is how Ambani legally bought India's most valuable land at 98% discount."

## FINAL SCRIPT

"Mukesh Ambani bought 100,000 crore rupees worth of land for just 2,200 crore rupees."

And he did it legally.

Here's the crazy story of how he made it happen.

Instead of buying the land directly, Ambani made a genius move. He bought 74 percent stake in a company called NMIIA, at just 28.50 rupees per share which owned the land.

Now here's where it gets interesting.

This massive 5,286-acre land in Navi Mumbai sits next to a new international airport, India's largest port, the Atal Setu, and the Mumbai-Pune Highway.

The masterstroke? Reliance had already invested 6,162 crore rupees in this project, making them the largest creditor. So when CIDCO waived its first right of refusal, the deal was sealed.

Think about it: Land worth 100,000 crore rupees, acquired for just 2,200 crore rupees, through perfect corporate planning.

This could be Mukesh Ambani's greatest chess move yet.

The question everyone's asking: What is Reliance planning to do with land bigger than 4,000 football fields?

Comment your theories below and follow for more untold business stories."""
    },

    # 5. Ambani Killed Dunzo
    {
        "title": "Ambani Killed Dunzo",
        "mode": "informational",
        "hook_type": "story",
        "content": """## HOOK OPTIONS

HOOK 1:
"Mukesh Ambani killed Dunzo. He did it by investing over 2000 crores in the company."

HOOK 2:
"Everyone thought Ambani lost money on Dunzo. But let me show you his evil genius masterplan."

HOOK 3:
"Ambani invested 2000 crores to destroy a company from inside. Here's his plan."

HOOK 4:
"This is how Mukesh Ambani legally eliminated his competition using their own company."

HOOK 5:
"Ambani's 2000 crore investment was never meant to save Dunzo. It was designed to kill it."

## FINAL SCRIPT

"Mukesh Ambani killed Dunzo."

He did by investing over 2000 crores in the company.

Everyone thought Ambani lost money on Dunzo. But let me show you his evil genius masterplan with which he made 10s of thousands of crores.

Let's look at step 1 of Ambani's trap.

Find a desperate company. Invest 2000 crores. Get a board seat. Access all data.

Simple. Right?

But wait. It gets better.

Here's where Ambani showed his 200 IQ moves.

First. He blocked other investors. Then. Refused to lower valuation. Next. Set impossible targets. And watched them burn 100 crores every month.

While everyone thought he was losing money. He was actually executing his master plan.

Want to know what Ambani REALLY got for 2000 crores?

Complete market research. Best talent pool. Customer data worth thousands of crores. Competitor's playbook. Tech stack insights.

And then. Came the master stroke.

While Dunzo was dying: JioMart grew 400 percent. They copied their best features. Hired their top talent. Took their market share.

Ambani wasn't failing. He was feasting.

Need proof?

Dunzo went from 2000 to just 50 employees. All founders resigned. 18 months of unpaid salaries.

Meanwhile. JioMart? Became a 80,000 crore giant.

This wasn't just business. This was Ambani's Art of War.

Remember this. Sometimes the biggest companies don't compete. They invest. And eliminate.

Have you tried Dunzo? Let me know in comments and do follow me for such insightful breakdowns."""
    },

    # 6. House in Italy
    {
        "title": "House in Italy 85 Rupees",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"You can buy this house in Italy for just 85 rupees."

HOOK 2:
"Italian towns are literally selling beautiful houses for the price of your chai."

HOOK 3:
"This centuries-old Italian home costs 85 rupees. Here's the catch and the opportunity."

HOOK 4:
"Italy is selling homes for 85 rupees to anyone in the world. Including Indians."

HOOK 5:
"One Indian bought a house in Italy for 85 rupees. Now earns 1.5 lakhs monthly from it."

## FINAL SCRIPT

"You can buy this house in Italy for just 85 rupees."

Not just this home, even this, this and 100s more.

No, this isn't clickbait.

Italian towns are literally selling beautiful houses for the price of your chai. But the reason why they are doing it is genius.

See, hundreds of beautiful Italian villages are slowly becoming ghost towns. Young people are leaving for big cities. And thousands of historic homes are sitting empty.

These aren't just any homes. We're talking about centuries old Italian architecture.

But here's where it gets interesting. These towns came up with a genius plan. They're selling homes to anyone in the world. Including Indians. For just 85 rupees.

Now here's the plot twist. You'll need about 20 to 40 lakhs for renovations. And you must finish them in 3 years.

But here's what most people don't know.

These towns are actually helping buyers. You get free architectural guidance. Fast tracked permits. Tax benefits for 5 years. And some towns even offer extra incentives for young families.

Let me tell you about Rahul from Mumbai. He bought one of these homes last year. Spent 25 lakhs on renovations. And he earns 1.5 lakhs monthly through Airbnb.

But that's not all. You can use these homes for remote work. Hello, European time zone clients. Or start a tourism business. Maybe plan for retirement. Or just have your dream Italian vacation home.

What a win win strategy right?

Would you be keen to grab one? Let me know. Do follow me for more such interesting things!"""
    },

    # 7. Apple Tax
    {
        "title": "Apple Tax iPhone Pricing",
        "mode": "informational",
        "hook_type": "negative",
        "content": """## HOOK OPTIONS

HOOK 1:
"Every iPhone user is paying a hidden tax that aren't aware of."

HOOK 2:
"If you're using an iPhone, you're paying up to 124% more for the exact same products."

HOOK 3:
"The exact same 500 grams of grapes on Zepto costs 65 rupees on Android and 146 rupees on iPhone."

HOOK 4:
"Apple users are secretly paying double. Here's proof you can verify right now."

HOOK 5:
"This hidden iPhone tax is costing Indian users lakhs every year."

## FINAL SCRIPT

"Every iPhone user is paying a hidden tax that aren't aware of."

Its called apple tax and it means you could be paying upto 100% more while buying the exact same product vs android or web.

Let me show you proof.

The exact same 500 grams of grapes on Zepto costs 65 rupees on Android and 146 rupees on iPhone.

But it's not just groceries.

On Flipkart, a Mokobara suitcase shows up at 4,119 rupees with a 65% discount on Android. The exact same suitcase on iPhone? 4,799 rupees with only a 60% discount.

And this is happening everywhere.

Ola and Uber charging more for the same route. Travel websites showing higher prices for the same flights. All because you're using an iPhone.

Why is this happening?

Two major reasons.

First, the Apple Tax - every time you make a purchase through an iPhone app, Apple takes 30% while Android takes 15%. And companies pass these charges directly to you.

Second, Companies see iPhone users as premium customers.

They assume if you can afford an iPhone, you can afford to pay more. So they show you higher prices and smaller discounts, all based on your phone choice.

The solution?

Always check prices on both Android and iPhone before purchasing.

Don't let companies charge you more just because of your phone choice.

Save this information - it might just save you from paying the Apple Tax. Follow for more insightful breakdowns!"""
    },

    # 8. Puma Strategy
    {
        "title": "Puma Marketing Recovery",
        "mode": "informational",
        "hook_type": "story",
        "content": """## HOOK OPTIONS

HOOK 1:
"A footballer threw these 20,000 rupee Puma boots in the dustbin during a live match."

HOOK 2:
"Puma's boots were thrown in the trash on live TV. What they did next was genius."

HOOK 3:
"This footballer publicly trashed Puma's premium boots. Puma's response went viral."

HOOK 4:
"Puma turned a PR nightmare into marketing gold in 24 hours. Here's how."

HOOK 5:
"Chelsea star threw Puma boots in dustbin. Puma's response became a marketing masterclass."

## FINAL SCRIPT

"A footballer threw these 20 thousand rupee Puma boots in the dustbin during a live match."

What Puma did next was absolute genius.

This could have been a complete disaster. Chelsea star Cucurella slipped twice wearing these brand new Puma boots, costing his team two goals. In front of millions watching live.

He didn't just change the boots - he ran to the bench mid-game, ripped them off, and later posted a photo of them in the trash.

Think about this: Millions of people just watched a professional footballer throw your premium product in the dustbin. Sales could have crashed overnight.

But Puma's response? Brilliant.

Within 24 hours, they posted a "Caution: Wet Floor" sign with Cucurella's signature bushy hair, and one perfect caption: "It's not how you slip, it's how you bounce back."

The internet exploded. Even rival players couldn't help but share it. A PR nightmare turned into marketing gold overnight.

The story gets even better - Cucurella scored his first Premier League goal in his next match, wearing Puma boots. You couldn't script it better.

For marketers watching this - sometimes your biggest crisis can become your biggest opportunity. It's all about how you respond.

Follow for more genius marketing moves that turn disasters into gold."""
    },

    # 9. Minimalist
    {
        "title": "Minimalist Brand Story",
        "mode": "informational",
        "hook_type": "story",
        "content": """## HOOK OPTIONS

HOOK 1:
"These two Indian founders are about to make Rs.2000 crores by selling their company they started just 4 years back."

HOOK 2:
"This skincare brand turned Rs.140 crores into Rs.3000 crores in 4 years. Zero marketing spend."

HOOK 3:
"HUL wants to buy this Indian brand for Rs.3000 crores. They built it with zero celebrity endorsements."

HOOK 4:
"Two founders disrupted a Rs.50,000 crore industry by doing the opposite of everyone else."

HOOK 5:
"This Indian skincare brand is profitable from Day 1. HUL is paying 3000 crores for it."

## FINAL SCRIPT

"These two Indian founders are about to make Rs.2000 crores by selling their company they started just 4 years back."

There's a good chance you're using their products.

Now before I reveal the brand name. Let me tell you what made them different.

Clean white packaging. No fancy claims. Chemical names right on front. Yes, the ones you can't pronounce.

While other brands were hiding ingredients in fine print, charging Rs.2000-3000, and pushing celebrity faces, they chose transparency:

Full ingredient list on front. Everything under Rs.700. Science over stardom.

Can you guess the brand?

Yes, we're talking about MINIMALIST! The brand that changed Indian skincare forever.

They raised Rs.140 crores. But unlike others who burn money on Bollywood faces, TV commercials, and heavy discounting, they invested in product research, quality ingredients, and making it available everywhere.

The results?

Rs.350 crore revenue. Profitable from Day 1. Doubled profits yearly. Millions of loyal customers. Zero marketing spend.

Now HUL wants to buy them for Rs.3000 CRORES!

Why such a high value? Because they built real brand value, unshakeable customer trust, and were profitable from the start.

Their success formula was simple: Simplicity over hype. Education over advertising. Trust over everything else. Product over promotion.

The truth is: Money can buy customers, but trust builds legacy.

Follow for more such insights. Save this for your startup journey."""
    },

    # 10. Tamil Nadu Women Employment
    {
        "title": "Tamil Nadu Women Empowerment",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"This Indian state has more working women than any other state."

HOOK 2:
"This Indian state is leading women empowerment. They were invited by Davos to teach the world."

HOOK 3:
"43% of all women working in India's manufacturing sector are in this one state alone."

HOOK 4:
"Davos invited this Indian state to share their women empowerment secrets."

HOOK 5:
"This state has 6.79 lakh women in manufacturing. That's 43% of India's total."

## FINAL SCRIPT

"This Indian state has more working women than any other state."

The crazy part? They were invited by Davos to teach the world how they're making it happen.

Davos is the world's most exclusive economic forum where billionaires, world leaders, and top CEOs meet to shape global policies. Even getting invited is HUGE.

Want to know which state?

Here's a hint... 43% of ALL women working in India's manufacturing sector are in this ONE state alone. That's 6.79 lakh women.

It's TAMIL NADU.

While other states are still figuring it out, Tamil Nadu's crushing records. Their rural areas? 35.5% women in workforce. That's 13% higher than their urban areas!

But here's what's mind-blowing... 64% of their women work in service and manufacturing, when the national average is just 43%. And they ranked number 2 in India for women-owned businesses!

No wonder they're launching Bullish on TN at Davos 2025, with 50 high-stakes meetings lined up. From 7 AM to 10 PM, for 3 straight days.

When the world's biggest economic forum says "Come teach us your secrets"... you know something special is happening.

Tamil Nadu isn't just participating in the global race... they're showing the world how it's done.

Double tap if you're proud of India's rise, and follow for more hidden gems of India's success."""
    },

    # 11. Ikea Strategy
    {
        "title": "Ikea Location Strategy",
        "mode": "informational",
        "hook_type": "question",
        "content": """## HOOK OPTIONS

HOOK 1:
"If you think Ikea stores are badly located then you don't know about the crazy marketing tactic they use."

HOOK 2:
"Ikea's inconvenient locations made them a $44 billion empire."

HOOK 3:
"Ikea deliberately puts stores 45 minutes from city centers. It's pure genius."

HOOK 4:
"This psychological trick makes Ikea customers spend 40% more."

HOOK 5:
"Ikea's location strategy costs them nothing but makes customers spend more."

## FINAL SCRIPT

"If you think Ikea stores are badly located then you don't know about the crazy marketing tactic they have been using which ends up making you spend 40% more."

IKEA's store locations aren't random - they're actually genius.

Most companies fight for prime city locations, but IKEA does the opposite.

The average IKEA store sits 45 minutes from city centers, surrounded by nothing but parking lots and highways.

This isn't a cost-cutting move - it's actually brilliant psychology. Here's how it works...

When you invest time and gas money to reach an IKEA, your brain activates something called the 'sunk cost fallacy.'

Your mind thinks: 'I've already spent so much effort getting here, I need to make this trip worth it.' This makes you more likely to fill your cart with items you weren't planning to buy.

But here's where IKEA's strategy gets even smarter...

They build massive showrooms in these locations - typically 300,000 square feet. The extra space costs way less because land is cheaper outside cities.

This means they can create entire room displays, letting you imagine the furniture in your home, making you more likely to purchase.

The result? IKEA's psychological strategy helped them build a $44 billion empire - by making their stores harder to reach.

Follow for more hidden business strategies that are changing the game."""
    },

    # 12. Wooly Mammoth
    {
        "title": "Wooly Mammoth Resurrection",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"This is a Wooly Mammoth. They are currently extinct. But this company is bringing them back."

HOOK 2:
"Jurassic Park is happening for real right now. This company is bringing extinct animals back."

HOOK 3:
"This company is bringing back woolly mammoths. We might see them by 2028."

HOOK 4:
"Scientists are using AI and genetic engineering to resurrect woolly mammoths."

HOOK 5:
"By 2028, woolly mammoths could walk the Earth again. Here's the company making it happen."

## FINAL SCRIPT

"This company is bringing back woolly mammoths."

Yes, the same creature that went extinct thousands of years ago. The one you've seen in your science textbooks next to dinosaurs.

But here's the craziest part - we might see them for real by 2028.

The company's called Colossal Biosciences, and they're using genetic engineering and AI to resurrect an extinct species.

Now you might be thinking - why mammoths? Why not dinosaurs?

Well, these weren't just giant furry elephants. They were Earth's natural climate engineers.

Here's what's wild. When mammoths roamed the Earth: Their massive feet packed down snow, preserving the permafrost. They knocked down trees, preventing forest overgrowth. They basically kept the Arctic frozen.

But when they disappeared, everything changed: The ground got soft. Forests grew unchecked. The Arctic started melting. Our climate shifted dramatically.

Now Colossal has a crazy plan to bring them back: 16 labs worldwide. Cutting-edge genetic tech. Advanced AI systems.

And they're not just working on mammoths. They've created an mRNA vaccine that's already saving modern elephants from a deadly virus.

They're saying by 2028, we could see actual woolly mammoths walking the Earth again, helping fight climate change just like they did thousands of years ago.

This isn't science fiction anymore. It's happening right now.

Do follow me for more such crazy AI breakthroughs."""
    },

    # 13. AI Pendant Friend
    {
        "title": "Friend AI Pendant",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"You see this device hanging on my neck. It's actually an AI device which will be your best friend."

HOOK 2:
"A 21-year-old Harvard dropout just launched an AI companion that costs just 9000 rupees."

HOOK 3:
"This AI pendant is always listening. And it costs less than an AirPod."

HOOK 4:
"This tiny pendant remembers every conversation you have. It costs 9000 rupees."

HOOK 5:
"Feeling lonely at 3 AM? This AI pendant is designed to be there. Always."

## FINAL SCRIPT

"You see this device hanging on my neck."

It is actually an AI device which will be your best friend in the future.

The crazy part, it just costs about nine thousand rupees.

A 21-year-old Harvard dropout just launched something that's about to change everything.

It's called Friend.

Here's what makes it incredible.

It's always listening to every conversation, every thought you share, and every meeting you attend.

Then it texts you smart responses about your day, reminders of important moments, insights from conversations, and notes you spoke out loud.

Feeling lonely at 3 AM? Friend is there. Need to remember something? Just say it out loud. Important meeting? Every detail is captured.

It's like having a personal assistant, a memory keeper, and a 24/7 companion, all in one pendant.

Nine thousand rupees for an AI that never leaves your side, never misses a word, and always texts back.

Would you want an AI companion? Drop a comment if this blows your mind.

Follow for more future tech."""
    },

    # 14. Apple Listening
    {
        "title": "Apple Siri Recording Scandal",
        "mode": "informational",
        "hook_type": "negative",
        "content": """## HOOK OPTIONS

HOOK 1:
"I have some bad news for iPhone users. Your iPhone was recording your conversations."

HOOK 2:
"Apple was caught recording conversations and sending info to advertisers. They're paying 800 crores."

HOOK 3:
"Ever notice how you talk about something and suddenly see ads for it everywhere?"

HOOK 4:
"Apple Siri was secretly recording without anyone saying 'Hey Siri'. They got caught."

HOOK 5:
"The privacy-focused company was caught recording you. Apple is paying 800 crores fine."

## FINAL SCRIPT

"I have some bad news for iPhone users."

Your iPhone was recording your conversations and sending the information to advertisers.

All those times you saw ads for products you only talked about wasn't a coincidence.

Apple was caught doing that and is paying a fine of 800 crores.

Apple Siri was randomly recording private conversations. Without anyone saying hey Siri. And allegedly sharing those recordings with advertisers.

Here's the ironic part.

This is the same company that brags about privacy. The same one with those Privacy That's iPhone commercials.

While Apple denies everything. They still paid 95 million to make this go away.

Now here's the good news.

If you had any Siri device between 2014 and 2024. You could get up to 1800 rupees per device.

But more importantly.

Here's how to protect yourself.

Turn off Listen for Hey Siri. Disable Siri when locked. And check your microphone permissions.

Want proof your phone listens?

Try this. Pick something random like purple cowboy boots. Talk about it near your phone. Then watch your ads for the next day.

If this helped. Follow for more tech secrets they don't want you to know."""
    },

    # 15. Tesla Killing Uber
    {
        "title": "Tesla Robot Taxi Killing Uber",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"In the future, your car will make you lakhs while you're not using it."

HOOK 2:
"Elon Musk is trying to kill Uber, Ola, and every ride-sharing app."

HOOK 3:
"Tesla is building robot taxis. Your Tesla could make you 2 lakhs every month."

HOOK 4:
"500,000 car owners are already testing Tesla's self-driving robot taxi technology."

HOOK 5:
"Imagine your car making money while you sleep. Tesla is making it real."

## FINAL SCRIPT

"Elon Musk is trying to kill Uber, Ola, and every ride-sharing app."

And his solution? It's genius.

Imagine getting into a Tesla with no driver. No steering wheel.

But here's the crazy part.

Tesla is building an army of robot taxis that drive themselves.

And if you own a Tesla or plan to buy one? You're about to get rich.

Because while your car sits in the parking lot doing nothing. It could be making you 2 lakhs every single month.

Tesla has already convinced 500,000 car owners to test this technology.

And they've driven over 2 billion miles.

But Elon's master plan gets even better.

These robot taxis will cost less than half of what Uber charges.

Imagine millions of autonomous Teslas. Running 24/7. No drivers to pay. No breaks needed.

This isn't future tech anymore. It's happening now.

Would you trust a car with no driver? Let me know and follow for more future tech updates."""
    },

    # 16. Halo Dreams Device
    {
        "title": "Halo Dreams Controller",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"This tiny device on my head can help me decide what I want to see in my dreams everyday."

HOOK 2:
"You see these tiny devices on my head? They can literally control my dreams."

HOOK 3:
"You can become a super human with this device. It costs 8000 rupees to book."

HOOK 4:
"Tesla, Einstein made breakthroughs through lucid dreams. Now you can trigger them on demand."

HOOK 5:
"This AI-powered headband lets you control your dreams. Book it for 8000 rupees."

## FINAL SCRIPT

"This tiny device on my head can help me decide what I want to see in my dreams everyday!"

You can literally become a super human with this device.

The crazy part? You can book this today for about 8 thousand rupees.

If you're wondering how it does it, it leverages the power of lucid dreams.

But before I tell you why lucid dreams are extremely powerful, let me introduce you to Prophetic. A neuroscience company that's changing dream technology forever.

Their device is called The Halo, and it's the world's first AI-powered dream controller.

In normal dreams, your brain's control center is completely off. That's why you can't control when you're being chased by monsters or falling off cliffs.

But lucid dreams are different. Tesla, Einstein, and other geniuses made their biggest breakthroughs through lucid dreams.

The only problem is that they couldn't control when these dreams happened.

The Halo changes everything.

Using precise ultrasonic waves to target your brain's dream control center, it lets you trigger lucid dreams on demand.

Imagine testing dangerous experiments, practicing any skill, or solving impossible problems - all while sleeping safely in your bed.

You can book Prophetic's Halo for just 8000 rupees, while the whole device costs upto one lakh rupees.

Drop a comment if you'd try dream control.

Follow for more such future tech breakdowns."""
    },

    # 17. 2 Crore Juice Shop
    {
        "title": "2 Crore Juice Shop Pune",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"This juice shop makes almost 2 crore rupees working just 4 hours a day."

HOOK 2:
"Pune entrepreneur works 5 AM to 9 AM only. Makes 2 crore yearly from juice."

HOOK 3:
"60 juice counters. 4 hours daily. 2 crore revenue. Here's the genius strategy."

HOOK 4:
"Most juice shops work 12 hours. This one works 4 hours and makes 2 crore."

HOOK 5:
"Indian juice seller built 2 crore business by targeting morning joggers only."

## FINAL SCRIPT

"This juice shop makes almost 2 crore rupees working just 4 hours a day."

Sounds impossible, right?

This Pune entrepreneur cracked the code, and its genius.

Most people work over 12 hours, fighting for the same customers.

But this guy? He did something completely different.

Instead of one big fancy shop, he started tiny portable juice counters near parks and running tracks.

Here is where it gets interesting.

He only operates from 5 AM to 9 AM, when most shops are still closed. Targeting morning joggers when they are craving something healthy.

And it gets better.

He did not stop at one counter.

He expanded to 60 plus locations. Each making 1000 rupees daily, with just 400 rupees in costs, and 300 rupees for staff.

That is 300 rupees profit, per counter, per day, times 60 plus locations.

The math is insane.

Let me break it down. 1.96 crore yearly revenue. 60 lakh pure profit. All from working just 4 hours daily.

Here is the real business lesson.

Success is not about working longer hours. It is about finding the right timing and the right audience.

What's your take on this strategy? Follow for more business breakdowns."""
    },

    # 18. Reva Story
    {
        "title": "Reva Electric Car Story",
        "mode": "informational",
        "hook_type": "story",
        "content": """## HOOK OPTIONS

HOOK 1:
"Every Indian needs to know this. India had electric cars before Elon Musk founded Tesla."

HOOK 2:
"India had electric cars on the road even before Elon Musk founded Tesla."

HOOK 3:
"In 2001, an Indian company built EVs. 2 years before Tesla even existed."

HOOK 4:
"This tiny Indian car was in 26 countries before Tesla sold a single vehicle."

HOOK 5:
"India's first EV cost less than a Tesla's down payment. It conquered London streets."

## FINAL SCRIPT

"Every Indian needs to know this."

India had electric cars on the road even before Elon Musk founded Tesla.

And we're not talking about prototypes.

These cars were actually conquering India and London streets while Elon was still busy with PayPal.

In 2001, a tiny Indian company built something revolutionary. 2 years before Tesla even existed!

But here's where it gets crazy.

While everyone said EVs would fail, this 740kg Indian car was already in 26 countries. Had over 1000 units in London alone. And cost less than a Tesla's down payment.

But who built it?

Chetan Maini, a young Indian engineer behind it spent 7 years developing this car. When the world thought EVs were impossible.

Can you guess the name of the company?

Its REVA. India's first EV revolution that shocked the auto industry.

Fun fact. I actually rode in one as a kid in Bangalore. It felt magical, this tiny silent car gliding through the streets.

And guess what? You can still spot these pioneers on Bangalore's lanes today!

The craziest part?

Mahindra bought the company in 2010. Making it India's first successful EV startup. Before startups were even a thing!

Have you come across Reva cars? Let me know in comments and Follow for more hidden Indian tech stories."""
    },

    # 19. AI Dog Collar
    {
        "title": "AI Dog Collar Petpuls",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"This AI collar can make any dog talk like a human."

HOOK 2:
"Ever wished you could have a real conversation with your dog? This AI collar makes it possible."

HOOK 3:
"This collar translates your dog's barks into emotions. It works on cats too."

HOOK 4:
"10,000 bark samples from 50 breeds trained this AI to understand your dog."

HOOK 5:
"India's pet care market is booming. This AI collar could be the next big opportunity."

## FINAL SCRIPT

"This AI collar can make any dog talk like a human."

Just like this.

The Petpuls collar is designed to analyze a dog's barks and translate them into one of five emotional states: happy, relaxed, anxious, angry, or sad.

This technology is based on a database of over 10,000 bark samples from more than 50 breeds of dogs.

The collar employs voice recognition technology to monitor and interpret these vocalizations, sending the analyzed data to a smartphone app for owners to track their dog's mood and activity levels.

But here's where it gets interesting.

Some owners say it perfectly matches their dog's attitude.

And, it works on cats too.

The pet care industry in India is experiencing a massive boom.

The Indian pet care market is expected to reach $490 million by 2025. Urban pet parents are spending 3x more on their pets compared to 5 years ago.

Premium pet products like this AI collar could revolutionize how we understand and care for our pets.

This is the right time to invest in Petcare industry or even start a new business.

Follow me for daily future tech updates."""
    },

    # 20. Aretto Shoes
    {
        "title": "Aretto Expanding Shoes",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"Hardik Pandya invested 550 thousand dollars in these expanding shoes for Kids."

HOOK 2:
"Parents buy 4 pairs of shoes every year for their child. These 2 founders fixed it with one pair."

HOOK 3:
"The average Indian parent buys 4 pairs yearly spending Rs.15,000+. These shoes grow with the child."

HOOK 4:
"These shoes expand up to 3 sizes as your child grows. Hardik Pandya invested in them."

HOOK 5:
"Two Pune students invented shoes that grow with your child. Raised Rs.4.5 crore."

## FINAL SCRIPT

"Hardik Pandya invested 550 thousand dollars in these expanding shoes for Kids."

The average Indian parent buys 4 pairs yearly. Spending Rs.15,000+ on shoes that become useless in weeks.

Two Pune students found a shocking solution.

Their invention adapts as your child grows.

Children's feet grow 3-4 sizes yearly. Traditional shoes can't adapt. Parents are forced to buy new pairs constantly.

But then... Aretto created India's first expanding shoes.

Using two groundbreaking technologies:

1. Expandable sole (grows upto 3 sizes)
2. "Infinite" fabric upper

They raised Rs.4.5 crore funding and they're so good that cricket star Hardik Pandya invested in them.

And 5000+ parents are already obsessed.

Just think about it:

No more shoe shopping every few months. Save like Rs.10,000+ yearly. And the best part? Your kid's feet stay healthy.

Save this if you're a parent and follow for more such business breakdowns."""
    },

    # 21. Space Selfie
    {
        "title": "Space Selfie Satellite",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"Check this out - this YouTuber built a satellite that takes your selfie while you're waving from Earth."

HOOK 2:
"This YouTuber is building a personal satellite to take selfies from space."

HOOK 3:
"A former NASA engineer is launching a satellite. You can use it to take selfies from space."

HOOK 4:
"This satellite will photograph you from space with Earth in the background."

HOOK 5:
"SATGUS satellite launches in months. Upload your photo and get a space selfie."

## FINAL SCRIPT

"Check this out - this YouTuber built a satellite that takes your selfie while you're waving from Earth."

Let me tell you how you can get a space selfie.

But before that you should know about the crazy tech he invented to make it happen.

It's insane.

This is Mark, a former NASA engineer turned YouTuber who's launching a satellite called SATGUS that takes photos of you from space with Earth photobombing in the background.

Now in order to make the satellite functional, he had to solve a bunch of major challenges.

One is power - he designed special solar panels that can fully charge a phone 9 times in just a 90-minute orbit.

But here's where it gets really crazy - he invented this reaction wheel system with three spinning flywheels that lets the satellite rotate precisely in any direction without thrusters.

It's pretty nuts, but the craziest part of all is that he's been documenting the whole journey.

After 3 years of development, the satellite's about to launch into orbit in just a couple months.

The coolest part?

When it's up there, you'll be able to upload your photo, and it'll take your selfie from space when it passes over your city.

Would you like to get a selfie from space?

Let me know in the comments and do follow me for such crazy tech!"""
    },

    # 22. Hyderabad vs Bangalore
    {
        "title": "Hyderabad vs Bangalore Tech Hub",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"Google, Microsoft, and Apple are leaving Bangalore. Their new destination? Hyderabad."

HOOK 2:
"Bangalore is losing its crown as India's Silicon Valley. And it's happening faster than predicted."

HOOK 3:
"Hyderabad's startup funding is up 156%. Bangalore's dropped 19%."

HOOK 4:
"T-Hub 2.0 is a Rs.1000 crore mega-project. It's not in Bangalore."

HOOK 5:
"Hyderabad built wider roads, better metros, faster permits. Tech giants are moving."

## FINAL SCRIPT

"Google, Microsoft, and Apple are leaving Bangalore. Their new destination? A city that was barely on the tech map 10 years ago."

For 40 years, Bangalore was untouchable in India's tech scene. The undisputed king of startups.

But in 2024, something changed. Startup funding dropped 19%. Traffic became unbearable. Office rent? Through the roof.

Meanwhile, 650 km away, another city was silently building something massive. Not just another tech hub. But a complete ecosystem.

Enter Hyderabad.

T-Hub 2.0: A Rs.1000 crore mega-project. World-class offices at half Bangalore's prices. And here's the genius part...

While Bangalore struggled with infrastructure, Hyderabad built wider roads, better metros, and faster permits.

The result?

Google, Microsoft, Uber - all moving their biggest R&D centers here. Startup funding? Up 156%.

But here's what everyone missed...

It wasn't just about buildings or funding. Hyderabad's success comes down to one thing: They didn't try to be the next Bangalore.

They created their own playbook. Focused on solving problems, not copying success.

The next tech hub won't win by copying Silicon Valley. It'll win by solving tomorrow's problems.

What city do you think is next?

Follow for more insights on India's changing tech landscape."""
    },

    # 23. Hybrid Animals Japan
    {
        "title": "Hybrid Animals Japan",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"Japan is creating these creatures in real. They are half human and half animal."

HOOK 2:
"What you are looking at right now are hybrids. Part human and part animal."

HOOK 3:
"Japan just made it legal to create new creatures. Part human, part animal."

HOOK 4:
"Scientists are combining human cells with animal embryos. Japan made it legal."

HOOK 5:
"These hybrids could end organ transplant waiting lists forever."

## FINAL SCRIPT

"Japan is creating these creatures in real."

They are half human and half animal created in a lab.

The reason why Japan is doing it would blow your mind.

Scientists are combining human cells with animal embryos, creating something that's never existed before in human history.

The ethics? Highly controversial. The potential? Absolutely mind-blowing.

You see, every single day, 17 people die waiting for organ transplants. Over 100,000 people sit on waiting lists, watching their time run out.

But these hybrids could change everything. Here's exactly how it works.

First, scientists take an animal embryo. Then, they remove specific genes that control organ development. Next, they insert human stem cells. Finally, they let it develop under strict supervision.

The result? An animal that can grow human organs inside it. Perfect matches. Zero rejection risk. No more endless waiting lists.

The world is completely divided on this. Some people call it unethical. Others say we're playing God.

But Japan's rules are incredibly strict. No human brain development is allowed. No reproductive experiments. The pure focus is on saving human lives.

Think about what this means. A child could get a new heart in weeks, not years.

The future isn't coming anymore. It's already here.

Hit follow for more groundbreaking science that's changing humanity."""
    },

    # 24. Pickleball
    {
        "title": "Pickleball India Rich Sport",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"Rich Indians are ditching cricket for a children's backyard game."

HOOK 2:
"In Mumbai, people are spending Rs.15,000 per hour just to play this American kid's game."

HOOK 3:
"The rich in Mumbai aren't playing golf anymore. They've switched to a backyard sport."

HOOK 4:
"This backyard game from 1965 is growing 400% faster than cricket in India."

HOOK 5:
"From zero courts to 1000+ courts. Pickleball is India's fastest-growing luxury sport."

## FINAL SCRIPT

"Rich Indians are ditching cricket for a children's backyard game."

You won't believe.

In Mumbai, people are spending Rs.15,000 per hour just to play this American kid's game from 1965.

And it's growing 400% faster than cricket in India.

In 1965, three dads in America couldn't find their badminton equipment. So they improvised with ping pong paddles and a plastic ball. They called it Pickleball.

But here's the crazy part: India had ZERO courts for this sport until 2023.

Plot twist: Today, there are 1000+ courts. 70,000+ players. And 40-50 new courts are being built every month.

But why is everyone obsessed?

Because unlike cricket or football, Pickleball lets you become a pro in months, not years. It's easier on your body than tennis. And takes less time than golf.

The elite caught on quickly: Last year's championship had a 1 crore prize pool. Private clubs are adding courts faster than ever. And CEOs are closing deals over Pickleball matches.

Here's what most people miss: This isn't just about sports. It's proof that sometimes the biggest opportunities come from the most unexpected places.

A game invented by bored dads is now India's fastest-growing luxury sport.

Follow for more hidden business opportunities hiding in plain sight."""
    },

    # 25. Seagliders
    {
        "title": "Seagliders IIT Madras",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"These IIT Madras students built this 'flying boat' that travels at 500km/h."

HOOK 2:
"This is a flying boat built by IIT Madras grads. Kolkata to Chennai in 3 hours for 600 rupees."

HOOK 3:
"Imagine flying just above water from Kolkata to Chennai for just Rs 600 in 3 hours."

HOOK 4:
"Anand Mahindra is obsessed with these flying boats from IIT Madras."

HOOK 5:
"These seagliders fly at 500 km/h. They could change how India travels."

## FINAL SCRIPT

"These IIT Madras students built this 'flying boat' that travels at 500km/h."

The crazy part, very soon for just 600 rupees you can travel from Kolkata to Chennai in just 3 hours.

That's the cost of a movie ticket and popcorn!

Kolkata to Chennai in just 3 hours? That's what these revolutionary "flying boats" from Waterfly Technologies promise to deliver.

But wait - these aren't boats or planes. They're "seagliders" that fly just 4 meters above water using something called ground effect.

Think of it as surfing on air cushions at speeds up to 500 km per hour! It also aims to offer ZERO carbon travel.

The craziest part?

Anand Mahindra himself is hyping them up, calling the design "stunning" and praising IIT Madras for rivaling Silicon Valley.

They already have a working prototype and by April 2025, a 100 kg version will be ready. By 2026, they'll have a full 20-seater glider in operation.

These electric seagliders don't just work over water. They can fly over ice, deserts - basically any flat surface without obstacles.

The real game-changer comes by 2029 when they plan to open intercontinental routes.

At just Rs 600 per seat for a journey that would cost thousands by plane, these seagliders could completely transform coastal travel.

Follow for more mind-blowing tech innovations that could change your life."""
    },

    # 26. 3D Printed House
    {
        "title": "3D Printed House Tvasta",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"This 2200 square foot luxury house in Pune was literally printed."

HOOK 2:
"These 3 IIT graduates literally printed this 2200 square foot luxury house in Pune."

HOOK 3:
"Like a regular printer, but with concrete. This house was printed, not constructed."

HOOK 4:
"Godrej challenged these IIT grads to prove 3D printed houses work. This is their answer."

HOOK 5:
"India could have 100 companies like this. The opportunity is massive."

## FINAL SCRIPT

"This 2200 square foot luxury house in Pune was literally printed."

Like a regular printer, but with concrete.

And it is changing how India builds homes.

Here is the wild part.

A massive 2200 square foot villa, created by a printer.

Think of a giant robotic arm, moving with millimeter precision, laying down concrete layer by layer.

The company behind this? A 3 crore rupee startup called Tvasta, founded by three IIT graduates.

But here is where it gets interesting.

They created a special concrete mix using industrial waste.

And the results? Mind blowing.

They finished the entire villa in just 4 months. With zero construction waste. And the homes use 50 percent less energy.

No one believed it was possible.

Even Godrej, one of India's biggest real estate giants, challenged them to prove it.

This house? This was their answer.

You see, traditional construction in India has a massive problem. 30 percent of materials go to waste. Projects face endless delays. And costs keep rising.

But now, major real estate companies are lining up to work with Tvasta.

There is a massive business opportunity here. Construction is a trillion dollar industry. And India could have 100 companies like this.

Do follow me for more such business insights."""
    },

    # 27. Fevicol Founder
    {
        "title": "Fevicol Founder Story",
        "mode": "informational",
        "hook_type": "story",
        "content": """## HOOK OPTIONS

HOOK 1:
"This man worked as a peon making Rs.50/month. Today his company is worth Rs.650 billion."

HOOK 2:
"If you think you need a fancy degree to build a billion-dollar company, this peon's story will shock you."

HOOK 3:
"A peon saw what billion-dollar companies missed. Built Rs.650 billion empire."

HOOK 4:
"This man turned Rs.50 monthly salary into Rs.650 billion company. No MBA. No connections."

HOOK 5:
"Fevicol's founder was a peon. His observation changed India's construction forever."

## FINAL SCRIPT

"This man worked as a peon making Rs.50 per month. Today his company is worth Rs.650 billion."

You're not gonna believe this story.

Back in the 1950s, there was this guy named Balvant Parekh.

Here's where it gets interesting. Every day, he'd watch carpenters struggle with messy animal-based glues. They'd have to heat it up. It was super inconvenient. And most vegetarians wouldn't even touch it.

Now, most people would just ignore this problem. But Balvant saw an opportunity everyone else missed.

Instead of accepting things as they were, he teamed up with his brother and started experimenting.

In 1959, they launched something revolutionary: Fevicol. A ready-to-use synthetic adhesive.

But the genius wasn't just the product. It was what they did next.

Instead of going to fancy stores, they went straight to the carpenters. Showed them how it worked. Made them brand ambassadors without spending a rupee.

The results? Today, Fevicol is so popular in India, people don't say "pass the adhesive." They say "pass the Fevicol" even when it's not Fevicol.

That's called brand genericization. And that's how you know you've made it.

His company now controls 70% of India's adhesive market. Worth Rs.650 billion.

Follow for more incredible Indian business stories."""
    },

    # 28. Brocode Beer
    {
        "title": "Brocode Beer Tax Hack",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"One word on this beer bottle saved Brocode crores of rupees."

HOOK 2:
"Brocode became India's hottest beer brand. But they don't even sell beer."

HOOK 3:
"This beer brand pays half the taxes by hiding one word on the bottle."

HOOK 4:
"Brocode sells wine disguised as beer. It's completely legal and pure genius."

HOOK 5:
"Look closely at a Brocode bottle. Something hidden saves them crores."

## FINAL SCRIPT

"One word on this beer bottle saved Brocode crores of rupees."

Brocode became one of India's hottest beer brands. But here's the crazy part.

They don't even sell beer.

Everyone orders Brocode thinking it's beer. That's exactly what they wanted.

Look closely at their bottle. Something's hidden in plain sight.

Brocode isn't beer at all. It's wine packaged as beer. With 15 percent alcohol, that's three times stronger than regular beer.

They also make sure it's placed next to beer instead of wine so the perception stays as beer.

But wait, it gets better.

On every bottle, they wrote Kraft Sekt. That's German for Craft Wine. They never even lied about it.

Here's the genius part.

In India, beer gets taxed two times more than wine.

So by selling wine as beer, they pay half the taxes while everyone thinks they're drinking beer.

This one move by Brocode created India's favorite party drink, saved crores in taxes, and stayed completely legal.

Sometimes the biggest business innovations are hiding in plain sight. Just in a different language.

Have you come across Brocode? Follow for more Indian business genius that changed the game."""
    },

    # 29. Deepseek AI
    {
        "title": "Deepseek AI China",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"OpenAI spent 100 million on GPT-4. This Chinese startup did it for 5 million."

HOOK 2:
"This Chinese AI just beat OpenAI, Google, and Meta. It cost 95% less to build."

HOOK 3:
"A Chinese hedge fund built an AI that's beating GPT-4. Silicon Valley is scared."

HOOK 4:
"Deepseek R1 matches GPT-4 but costs 95% less. Here's why OpenAI should worry."

HOOK 5:
"China just proved you don't need billions to build world-class AI."

## FINAL SCRIPT

"OpenAI spent 100 million on GPT-4. This Chinese startup did it for 5 million."

Silicon Valley is losing sleep over this.

Let me tell you about Deepseek R1, the AI that's changing everything we thought we knew about building AI.

While OpenAI, Google, and Meta pour billions into their models, a Chinese hedge fund built something just as powerful for a fraction of the cost.

Here's what's mind blowing.

Deepseek R1 matches GPT-4's performance in math, coding, and reasoning. But they did it with fewer resources, less computing power, and a tiny team.

The secret? They invented new training techniques that make AI smarter without throwing money at the problem.

For India, this is huge.

Our startups have always struggled with AI costs. GPU access is limited. Cloud computing is expensive. Big tech companies have seemed untouchable.

But Deepseek just proved something revolutionary. You don't need billions to build world-class AI.

Indian engineers are some of the best in the world. If a small Chinese team can challenge OpenAI, imagine what Indian startups could do with the right approach.

The AI race just got a lot more interesting.

Follow for more AI breakthroughs that could shape India's tech future."""
    },

    # 30. Meta Electricity
    {
        "title": "Meta Electricity Company",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"Meta is quietly becoming an electricity company. And no one's talking about it."

HOOK 2:
"Mark Zuckerberg is building power plants. Facebook needs more electricity than some countries."

HOOK 3:
"Meta just signed a deal for 4 gigawatts of power. That's enough for 3 million homes."

HOOK 4:
"Tech companies are becoming electricity companies. Meta's deal proves it."

HOOK 5:
"One data center now needs more power than New Orleans. Meta is planning ahead."

## FINAL SCRIPT

"Meta is quietly becoming an electricity company. And no one's talking about it."

Mark Zuckerberg just made a move that changes everything about how we think about tech companies.

Meta signed the world's largest corporate energy contract. 4 gigawatts of new power. That's enough electricity to power 3 million homes.

But why does a social media company need this much power?

Here's the thing most people don't realize.

One single data center now uses more electricity than the entire city of New Orleans. AI models are getting so powerful they need enormous amounts of energy to run.

And Meta isn't alone.

Google, Microsoft, Amazon - they're all in a race for power. Literally.

The AI revolution has created a new problem. These companies need more electricity than some small countries. And they can't just buy it from the grid anymore.

So they're becoming power companies themselves.

This is the hidden story of AI. Behind every ChatGPT query, every Instagram recommendation, every smart assistant - there's a massive demand for electricity.

The companies that solve the energy problem will win the AI race.

Follow for more hidden tech stories that explain what's really happening."""
    },

    # 31. Zuckerberg Threads
    {
        "title": "Zuckerberg Threads vs Twitter",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"Mark Zuckerberg panicked so hard he tried to buy a company with zero products for 32 billion dollars."

HOOK 2:
"Zuckerberg offered 32 billion for a company with no products. Here's why he was desperate."

HOOK 3:
"This story shows how scared Zuckerberg was of losing to Elon Musk."

HOOK 4:
"Meta tried to buy Twitter's replacement before building Threads. The deal fell apart."

HOOK 5:
"Before Threads existed, Zuckerberg was willing to pay 32 billion to beat Elon."

## FINAL SCRIPT

"Mark Zuckerberg panicked so hard he tried to buy a company with zero products for 32 billion dollars."

This is the story nobody talks about.

When Elon Musk bought Twitter, Zuckerberg saw an opportunity. Twitter was in chaos. Users were leaving. The perfect time to strike.

But instead of building something new, Zuckerberg did something desperate.

He tried to buy a company called Wunderkind. A startup that had raised money but had no actual product yet. Just an idea for a Twitter competitor.

The price? 32 billion dollars. For a company with zero users, zero revenue, and zero product.

Why would anyone pay that much for nothing?

Because Zuckerberg wanted to move fast. Building Threads from scratch would take time. Buying a team with a plan was quicker.

The deal fell apart. Wunderkind's founders wanted to stay independent.

So Zuckerberg had no choice. He built Threads in just 4 months. It became the fastest app to reach 100 million users in history.

But this story reveals something important about big tech.

Even the richest companies in the world panic. Even Zuckerberg makes desperate moves. And sometimes, being forced to build yourself turns out better than buying.

Follow for more untold tech stories."""
    },

    # 32. Andrej Karpathy
    {
        "title": "Andrej Karpathy AI Tool",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"Tesla's former AI director just dropped a tool that forces GPT, Claude, and Grok to judge each other."

HOOK 2:
"This ex-Tesla AI genius built a tool to make AI models compete. It's free."

HOOK 3:
"Andrej Karpathy left Tesla and OpenAI. His new tool is genius."

HOOK 4:
"Want to know which AI is actually best? This tool makes them battle it out."

HOOK 5:
"The man who built Tesla's Autopilot AI just dropped the ultimate AI testing tool."

## FINAL SCRIPT

"Tesla's former AI director just dropped a tool that forces GPT, Claude, and Grok to judge each other."

And it's completely free for anyone to use.

Meet Andrej Karpathy. He built Tesla's Autopilot AI. He was one of the founding members of OpenAI. He's basically AI royalty.

And he just created something brilliant.

It's called Chatbot Arena. Here's how it works.

You ask any question. Two random AI models answer it. But you don't know which model is which. You pick the winner based on the answer alone.

No brand names. No bias. Just pure quality comparison.

The results are fascinating.

Thousands of people have voted. And some expensive models are losing to free ones. Some new models are beating established giants.

For developers and businesses, this is gold.

Instead of paying for the most expensive AI, you can see which one actually performs best for your needs.

The tool is completely open source. Anyone can use it. Anyone can contribute.

This is how AI should be evaluated. Not by marketing. Not by hype. By actual performance judged by real users.

Follow for more AI tools that actually matter."""
    },

    # 33. Google Nuclear
    {
        "title": "Google Nuclear Power AI",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"Google just bought nuclear power for their AI. The energy problem is getting real."

HOOK 2:
"AI needs so much electricity that Google is going nuclear. Literally."

HOOK 3:
"Google signed a deal for nuclear reactors. AI's energy hunger is insane."

HOOK 4:
"The AI revolution has a dirty secret. It needs more power than most countries."

HOOK 5:
"Google, Amazon, Microsoft are all buying nuclear power. AI is that energy hungry."

## FINAL SCRIPT

"Google just bought nuclear power for their AI. The energy problem is getting real."

This isn't science fiction. It's happening right now.

Google signed a deal to get electricity from small nuclear reactors. Not solar. Not wind. Nuclear.

Why? Because AI is incredibly power hungry.

Training one large AI model uses as much electricity as 100 American homes use in a year. And that's just training. Running the model for millions of users? Even more.

Google isn't alone.

Amazon just invested in nuclear power. Microsoft is exploring the same. These companies see the future. And the future needs a lot of electricity.

Here's what this means for the world.

Nuclear energy is controversial. It's powerful but risky. The fact that tech giants are betting on it shows how desperate the situation is getting.

For India, this is a warning and an opportunity.

Our energy infrastructure isn't ready for the AI revolution. But countries that figure out clean, reliable power will win the AI race.

The AI future isn't just about algorithms. It's about electricity.

Follow for more insights on AI's hidden challenges."""
    },

    # 34. Sam Altman Stargate
    {
        "title": "Sam Altman Stargate Project",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"Sam Altman is secretly building a new AI model that's crushing every competitor."

HOOK 2:
"OpenAI's Stargate project will cost 500 billion dollars. Here's what they're building."

HOOK 3:
"This is the most expensive tech project in history. Sam Altman is behind it."

HOOK 4:
"Stargate will use more electricity than some countries. OpenAI is building it anyway."

HOOK 5:
"500 billion dollars for one AI project. Sam Altman convinced investors it's worth it."

## FINAL SCRIPT

"Sam Altman is secretly building a new AI model that's crushing every competitor."

It's called Stargate. And it's the most ambitious tech project in history.

The numbers are insane. 500 billion dollars in investment. That's more than the GDP of most countries. For one AI project.

What are they building?

A network of data centers so powerful they'll need their own power plants. AI models so advanced they'll make today's ChatGPT look like a calculator.

Sam Altman has a vision. He believes artificial general intelligence, AI that can do anything a human can, is coming soon. And he wants OpenAI to build it first.

The project will create 100,000 jobs in America. It'll need more electricity than many countries use. And it'll push the boundaries of what technology can achieve.

For India, this raises important questions.

Where do we stand in the AI race? Are we building infrastructure for the future? Or are we going to be left behind?

The Stargate project shows what's possible when money, talent, and ambition come together. The question is: who else will rise to the challenge?

Follow for more on the AI future being built right now."""
    },

    # 35. NotebookLM
    {
        "title": "NotebookLM Google AI",
        "mode": "informational",
        "hook_type": "shock",
        "content": """## HOOK OPTIONS

HOOK 1:
"Google just dropped an AI that turns any document into a podcast. For free."

HOOK 2:
"This AI reads your notes and creates a conversation about them. It's wild."

HOOK 3:
"NotebookLM is Google's secret weapon. Upload anything, get a podcast."

HOOK 4:
"Students are using this AI to study. It turns textbooks into conversations."

HOOK 5:
"Google built an AI that makes two hosts discuss your documents. It's free."

## FINAL SCRIPT

"Google just dropped an AI that turns any document into a podcast. For free."

This is NotebookLM. And it's changing how people learn.

Here's how it works. You upload any document. A PDF. A website. Your notes. Even a YouTube video.

The AI reads everything. Then it creates a podcast. Two AI hosts discuss your content like it's a radio show.

The voices sound human. The conversation flows naturally. And it actually makes complex topics easier to understand.

Students are going crazy for this.

Instead of reading a 100-page textbook, you can listen to a 15-minute conversation that covers the key points.

Researchers are using it to quickly understand papers. Professionals are using it to digest long reports.

The best part? It's completely free.

For India's students, this is huge. English educational content just became more accessible. Complex topics in science, history, business - all can become easy listening.

Google buried this feature inside a research tool. But it might be one of the most useful AI features they've ever made.

Try it yourself and let me know what you think.

Follow for more AI tools you probably don't know about."""
    },

    # 36. OpenAI Cost Cutting
    {
        "title": "OpenAI Free Tier Limits",
        "mode": "informational",
        "hook_type": "negative",
        "content": """## HOOK OPTIONS

HOOK 1:
"OpenAI is quietly limiting free users. The golden age of free AI might be ending."

HOOK 2:
"ChatGPT free users are getting slower responses. Here's why."

HOOK 3:
"OpenAI burns 8 million dollars a day. Free users are feeling the pressure."

HOOK 4:
"The company that made AI accessible is now restricting access. The irony is painful."

HOOK 5:
"Free ChatGPT is getting worse. OpenAI's costs are too high."

## FINAL SCRIPT

"OpenAI is quietly limiting free users. The golden age of free AI might be ending."

Something is changing at OpenAI. And most people haven't noticed.

Free ChatGPT users are reporting slower responses. Fewer features. More prompts to upgrade.

Why? Because OpenAI burns through 8 million dollars every single day.

Running AI is incredibly expensive. Every query costs money. Every conversation uses computing power. And OpenAI has over 100 million users.

The math doesn't work.

They raised billions in funding. But they're still losing money fast. And investors want returns.

So what's happening?

Free users are slowly being pushed towards paid plans. The quality gap between free and paid is growing. Premium features that were once available to everyone are disappearing.

For India, where most users rely on free tools, this matters.

The companies building AI want everyone to use it. But they also need to make money. This tension will define the next few years of AI.

The question is: will AI remain accessible? Or will the best tools become expensive luxuries?

Follow for more honest takes on what's really happening in AI."""
    },

    # 37. Elon vs OpenAI
    {
        "title": "Elon Musk vs OpenAI Battle",
        "mode": "informational",
        "hook_type": "story",
        "content": """## HOOK OPTIONS

HOOK 1:
"Elon Musk helped create OpenAI. Now he's trying to destroy it. Here's the full story."

HOOK 2:
"The bitter fight between Elon and Sam Altman is getting ugly. And it started with good intentions."

HOOK 3:
"Elon gave OpenAI millions. Now he wants it all back. This is getting interesting."

HOOK 4:
"OpenAI was supposed to save humanity. Now its founders are at war."

HOOK 5:
"From partners to enemies: The Elon Musk and Sam Altman story."

## FINAL SCRIPT

"Elon Musk helped create OpenAI. Now he's trying to destroy it. Here's the full story."

This is one of tech's biggest betrayals.

In 2015, Elon Musk was worried about AI. He thought Google was too powerful. So he helped create OpenAI as a nonprofit to keep AI safe and open.

He gave millions of dollars. His name. His credibility.

But things changed.

OpenAI needed more money. A lot more. So they created a for-profit company. Microsoft invested 10 billion dollars. And suddenly, the nonprofit became very profitable.

Elon felt betrayed.

He had helped create something meant to benefit humanity. Now it was a cash machine for Microsoft and Sam Altman.

So he fought back. He filed lawsuits. He created his own AI company, xAI. He launched Grok to compete with ChatGPT.

The battle is getting ugly.

Elon claims OpenAI broke its promises. OpenAI says Elon is just jealous. Both sides are throwing dirt.

For the rest of us, this matters.

The fight will shape how AI develops. Who controls it. Who profits. And whether it stays open or becomes locked up.

The irony? A company created to save humanity from AI might tear itself apart first.

Follow for more on the battle shaping our AI future."""
    }
]


def seed_database():
    """Seed the vector database with winning scripts."""
    print("\n" + "="*60)
    print("   SEEDING VECTOR DATABASE WITH WINNING SCRIPTS")
    print("="*60 + "\n")

    success_count = 0
    fail_count = 0

    for i, script in enumerate(WINNING_SCRIPTS, 1):
        try:
            # Extract hook from content
            hook_start = script["content"].find('HOOK 1:\n"') + 9
            if hook_start == 8:  # Not found with newline
                hook_start = script["content"].find('HOOK 1:\n"') + 9
            hook_end = script["content"].find('"', hook_start)
            hook_text = script["content"][hook_start:hook_end] if hook_start > 8 else ""

            # Generate skeleton
            skeleton_text = generate_skeleton(script["content"])

            # Convert strings to enums
            mode_enum = MODE_MAP.get(script["mode"], ScriptMode.INFORMATIONAL)
            hook_type_enum = HOOK_TYPE_MAP.get(script["hook_type"], HookType.SHOCK)

            # Add to database
            script_id = add_script_to_db(
                title=script["title"],
                full_text=script["content"],
                mode=mode_enum,
                hook_type=hook_type_enum,
                skeleton_text=skeleton_text,
                hook_text=hook_text
            )
            print(f"[{i:02d}/37] OK: {script['title']}")
            success_count += 1

        except Exception as e:
            print(f"[{i:02d}/37] FAIL: {script['title']} - {str(e)[:50]}")
            fail_count += 1

    print("\n" + "="*60)
    print(f"   SEEDING COMPLETE")
    print(f"   Success: {success_count} | Failed: {fail_count} | Total: {len(WINNING_SCRIPTS)}")
    print("="*60 + "\n")


if __name__ == "__main__":
    seed_database()
